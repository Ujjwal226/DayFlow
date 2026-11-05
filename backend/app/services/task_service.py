import logging
import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse
from app.schemas.task import (
    SubtaskCreateRequest,
    SubtaskProgressResponse,
    SubtaskResponse,
    SubtaskUpdateRequest,
    TaskCategoryAssignmentRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatisticsResponse,
    TaskTagsAssignmentRequest,
    TaskUpdateRequest,
)

logger = logging.getLogger("dayflow.tasks")


class TaskService:
    """Business logic and validation service for task management, categories, tags, and subtasks."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TaskRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.tag_repo = TagRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    @staticmethod
    def _is_task_overdue(task: Task, now: Optional[datetime] = None) -> bool:
        """Dynamically compute if a task is overdue without storing it permanently."""
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return False
        if not task.due_date:
            return False
        current_time = now or datetime.now(timezone.utc)
        due = task.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return due < current_time

    @classmethod
    def _calculate_subtask_progress(cls, subtasks: List[Task]) -> SubtaskProgressResponse:
        """
        Dynamically calculate subtask progress.
        Formula: completed_subtasks / total_subtasks * 100.
        If no subtasks, returns 0.0%.
        """
        if not subtasks:
            return SubtaskProgressResponse(
                total_subtasks=0,
                completed_subtasks=0,
                remaining_subtasks=0,
                progress_percentage=0.0,
            )
        total = len(subtasks)
        completed = sum(1 for st in subtasks if st.status == TaskStatus.COMPLETED)
        remaining = total - completed
        percentage = round((completed / total) * 100.0, 1) if total > 0 else 0.0
        return SubtaskProgressResponse(
            total_subtasks=total,
            completed_subtasks=completed,
            remaining_subtasks=remaining,
            progress_percentage=percentage,
        )

    def _to_subtask_response(self, subtask: Task) -> SubtaskResponse:
        """Convert a subtask model instance into SubtaskResponse."""
        is_overdue = self._is_task_overdue(subtask)
        return SubtaskResponse(
            id=subtask.id,
            user_id=subtask.user_id,
            parent_task_id=subtask.parent_task_id,  # type: ignore
            title=subtask.title,
            description=subtask.description,
            status=subtask.status,
            priority=subtask.priority,
            start_date=subtask.start_date,
            due_date=subtask.due_date,
            completed_at=subtask.completed_at,
            is_archived=subtask.is_archived,
            is_overdue=is_overdue,
            created_at=subtask.created_at,
            updated_at=subtask.updated_at,
        )

    def _to_response(self, task: Task) -> TaskResponse:
        """Convert a Task model instance into a TaskResponse with category, tags, and progress."""
        is_overdue = self._is_task_overdue(task)
        category_resp = CategoryResponse.model_validate(task.category) if task.category else None

        tag_resps = [TagResponse.model_validate(t) for t in (task.tags or [])]

        raw_subtasks = task.subtasks or []
        subtask_resps = [self._to_subtask_response(st) for st in raw_subtasks]
        progress = self._calculate_subtask_progress(raw_subtasks)

        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            parent_task_id=task.parent_task_id,
            category_id=task.category_id,
            category=category_resp,
            project_id=task.project_id,
            recurring_task_id=task.recurring_task_id,
            occurrence_date=task.occurrence_date,
            occurrence_index=task.occurrence_index,
            tags=tag_resps,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            start_date=task.start_date,
            due_date=task.due_date,
            completed_at=task.completed_at,
            is_archived=task.is_archived,
            is_overdue=is_overdue,
            progress=progress,
            subtasks=subtask_resps,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def create_task(self, user_id: uuid.UUID, payload: TaskCreateRequest) -> TaskResponse:
        """Create a new personal task belonging strictly to user_id."""
        now = datetime.now(timezone.utc)
        completed_at = now if payload.status == TaskStatus.COMPLETED else None

        # Verify category ownership if provided
        if payload.category_id:
            category = self.cat_repo.get_by_id(payload.category_id, user_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found.",
                )

        # Verify project ownership if provided
        if payload.project_id:
            project = self.proj_repo.get_by_id(payload.project_id, user_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found.",
                )

        # Verify tag ownership if provided
        tags = []
        if payload.tag_ids:
            tags = self.tag_repo.get_by_ids(payload.tag_ids, user_id)
            if len(tags) != len(set(payload.tag_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tags not found.",
                )

        task = Task(
            user_id=user_id,
            category_id=payload.category_id,
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            completed_at=completed_at,
            is_archived=False,
            tags=tags,
        )
        try:
            created = self.repo.create(task, commit=False)
            logger.info("Created task id=%s for user_id=%s", created.id, user_id)

            # Log TASK_CREATED activity
            from app.models.activity_log import ActivityLog
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    task_id=created.id,
                    recurring_task_id=created.recurring_task_id,
                    entity_type=ActivityEntityType.TASK.value,
                    entity_id=created.id,
                    action=ActivityAction.TASK_CREATED.value,
                    changes=None,
                    extra_metadata={
                        "title": created.title,
                        "priority": created.priority.value if hasattr(created.priority, "value") else str(created.priority),
                        "status": created.status.value if hasattr(created.status, "value") else str(created.status),
                    },
                ),
                commit=False,
            )

            self.db.commit()

            # Re-fetch with relations loaded
            full_task = self.repo.get_by_id(created.id, user_id)
            return self._to_response(full_task or created)
        except Exception:
            self.db.rollback()
            raise

    def get_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        """Retrieve task by id strictly owned by user_id."""
        task = self.repo.get_by_id(task_id, user_id)
        if not task:
            logger.warning("Task not found or access denied: task_id=%s user_id=%s", task_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        return self._to_response(task)

    def update_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: TaskUpdateRequest,
    ) -> TaskResponse:
        """Partially update a task strictly owned by user_id."""
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        # Check date relationship if either or both are being modified
        new_start = payload.start_date if "start_date" in payload.model_fields_set else task.start_date
        new_due = payload.due_date if "due_date" in payload.model_fields_set else task.due_date
        if new_start is not None and new_due is not None:
            cmp_start = new_start.replace(tzinfo=timezone.utc) if new_start.tzinfo is None else new_start
            cmp_due = new_due.replace(tzinfo=timezone.utc) if new_due.tzinfo is None else new_due
            if cmp_due < cmp_start:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Due date cannot be earlier than start date.",
                )

        # Capture original values for activity log diff
        changes = {}
        old_status = task.status
        old_title = task.title
        old_desc = task.description
        old_priority = task.priority
        old_start = task.start_date
        old_due = task.due_date
        old_cat_id = task.category_id
        old_proj_id = task.project_id
        old_tag_ids = sorted([str(t.id) for t in (task.tags or [])])

        # Validate category ownership if updating category
        if "category_id" in payload.model_fields_set:
            if payload.category_id is not None:
                category = self.cat_repo.get_by_id(payload.category_id, user_id)
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Category not found.",
                    )
            task.category_id = payload.category_id
            if old_cat_id != payload.category_id:
                changes["category_id"] = {"old": str(old_cat_id) if old_cat_id else None, "new": str(payload.category_id) if payload.category_id else None}

        # Validate project ownership if updating project
        if "project_id" in payload.model_fields_set:
            if payload.project_id is not None:
                project = self.proj_repo.get_by_id(payload.project_id, user_id)
                if not project:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Project not found.",
                    )
            task.project_id = payload.project_id
            if old_proj_id != payload.project_id:
                changes["project_id"] = {"old": str(old_proj_id) if old_proj_id else None, "new": str(payload.project_id) if payload.project_id else None}

        # Validate tag ownership if updating tags
        if "tag_ids" in payload.model_fields_set and payload.tag_ids is not None:
            tags = self.tag_repo.get_by_ids(payload.tag_ids, user_id)
            if len(tags) != len(set(payload.tag_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tags not found.",
                )
            task.tags = tags
            new_tag_ids = sorted([str(t.id) for t in tags])
            if old_tag_ids != new_tag_ids:
                changes["tag_ids"] = {"old": old_tag_ids, "new": new_tag_ids}

        if "title" in payload.model_fields_set and payload.title is not None:
            if old_title != payload.title:
                changes["title"] = {"old": old_title, "new": payload.title}
            task.title = payload.title
        if "description" in payload.model_fields_set:
            if old_desc != payload.description:
                changes["description"] = {"old": old_desc, "new": payload.description}
            task.description = payload.description
        if "priority" in payload.model_fields_set and payload.priority is not None:
            if old_priority != payload.priority:
                changes["priority"] = {
                    "old": old_priority.value if hasattr(old_priority, "value") else str(old_priority),
                    "new": payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
                }
            task.priority = payload.priority
        if "start_date" in payload.model_fields_set:
            if old_start != payload.start_date:
                changes["start_date"] = {"old": old_start.isoformat() if old_start else None, "new": payload.start_date.isoformat() if payload.start_date else None}
            task.start_date = payload.start_date
        if "due_date" in payload.model_fields_set:
            if old_due != payload.due_date:
                changes["due_date"] = {"old": old_due.isoformat() if old_due else None, "new": payload.due_date.isoformat() if payload.due_date else None}
            task.due_date = payload.due_date

        action_type = ActivityAction.TASK_UPDATED
        if "status" in payload.model_fields_set and payload.status is not None:
            new_status = payload.status
            if old_status != new_status:
                changes["status"] = {
                    "old": old_status.value if hasattr(old_status, "value") else str(old_status),
                    "new": new_status.value if hasattr(new_status, "value") else str(new_status),
                }
                if new_status == TaskStatus.COMPLETED:
                    action_type = ActivityAction.TASK_COMPLETED
                elif old_status == TaskStatus.COMPLETED and new_status != TaskStatus.COMPLETED:
                    action_type = ActivityAction.TASK_REOPENED

            task.status = new_status
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                task.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.COMPLETED and old_status == TaskStatus.COMPLETED:
                task.completed_at = None

        try:
            updated = self.repo.update(task, commit=False)
            logger.info("Updated task id=%s for user_id=%s", updated.id, user_id)

            # Log activity only if meaningful changes occurred
            if changes:
                from app.models.activity_log import ActivityLog
                self.activity_repo.create(
                    ActivityLog(
                        user_id=user_id,
                        actor_id=user_id,
                        task_id=updated.id,
                        recurring_task_id=updated.recurring_task_id,
                        entity_type=ActivityEntityType.TASK.value,
                        entity_id=updated.id,
                        action=action_type.value,
                        changes=changes,
                        extra_metadata={"title": updated.title},
                    ),
                    commit=False,
                )

            self.db.commit()

            full_task = self.repo.get_by_id(updated.id, user_id)
            return self._to_response(full_task or updated)
        except Exception:
            self.db.rollback()
            raise

    def assign_category(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: TaskCategoryAssignmentRequest,
    ) -> TaskResponse:
        """Assign or remove a category on a task."""
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        if payload.category_id is not None:
            category = self.cat_repo.get_by_id(payload.category_id, user_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found.",
                )
            task.category_id = payload.category_id
        else:
            task.category_id = None

        updated = self.repo.update(task, commit=True)
        full_task = self.repo.get_by_id(updated.id, user_id)
        return self._to_response(full_task or updated)

    def assign_tags(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: TaskTagsAssignmentRequest,
    ) -> TaskResponse:
        """Replace all tags assigned to a task."""
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        unique_ids = list(set(payload.tag_ids))
        tags = self.tag_repo.get_by_ids(unique_ids, user_id)
        if len(tags) != len(unique_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more tags not found.",
            )

        old_tag_ids = set(t.id for t in (task.tags or []))
        new_tag_ids = set(t.id for t in tags)

        added_ids = new_tag_ids - old_tag_ids
        removed_ids = old_tag_ids - new_tag_ids

        task.tags = tags
        updated = self.repo.update(task, commit=False)

        # Log individual tag assignment and removal events if changed
        from app.models.activity_log import ActivityLog
        for tag in tags:
            if tag.id in added_ids:
                self.activity_repo.create(
                    ActivityLog(
                        user_id=user_id,
                        actor_id=user_id,
                        task_id=task.id,
                        recurring_task_id=task.recurring_task_id,
                        entity_type=ActivityEntityType.TAG.value,
                        entity_id=tag.id,
                        action=ActivityAction.TAG_ASSIGNED.value,
                        extra_metadata={"tag_name": tag.name, "task_id": str(task.id), "task_title": task.title},
                    ),
                    commit=False,
                )

        old_tags_map = {t.id: t.name for t in (task.tags or [])}
        for rem_id in removed_ids:
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    task_id=task.id,
                    recurring_task_id=task.recurring_task_id,
                    entity_type=ActivityEntityType.TAG.value,
                    entity_id=rem_id,
                    action=ActivityAction.TAG_REMOVED.value,
                    extra_metadata={"tag_id": str(rem_id), "task_id": str(task.id), "task_title": task.title},
                ),
                commit=False,
            )

        self.db.commit()

        full_task = self.repo.get_by_id(updated.id, user_id)
        return self._to_response(full_task or updated)

    def delete_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> None:
        """Delete task strictly owned by user_id."""
        task = self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        # Snapshot task info before deletion to preserve audit history in activity log
        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=task.id,
                recurring_task_id=task.recurring_task_id,
                entity_type=ActivityEntityType.TASK.value,
                entity_id=task.id,
                action=ActivityAction.TASK_DELETED.value,
                changes=None,
                extra_metadata={
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority.value if hasattr(task.priority, "value") else str(task.priority),
                    "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                },
            ),
            commit=False,
        )

        self.repo.delete(task, commit=True)
        logger.info("Deleted task id=%s for user_id=%s", task_id, user_id)

    def duplicate_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        """
        Duplicate a task:
        Creates a new task copying title, description, priority, category, tags, and dates.
        Resets status to TODO, completed_at=None, is_archived=False.
        """
        source = self.repo.get_by_id(task_id, user_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        duplicated_title = f"{source.title} (Copy)"
        if len(duplicated_title) > 200:
            duplicated_title = duplicated_title[:193] + "... (Copy)"

        new_task = Task(
            user_id=user_id,
            category_id=source.category_id,
            project_id=source.project_id,
            title=duplicated_title,
            description=source.description,
            status=TaskStatus.TODO,
            priority=source.priority,
            start_date=source.start_date,
            due_date=source.due_date,
            completed_at=None,
            is_archived=False,
            tags=list(source.tags or []),
        )
        created = self.repo.create(new_task, commit=False)

        # Log TASK_DUPLICATED
        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=created.id,
                recurring_task_id=created.recurring_task_id,
                entity_type=ActivityEntityType.TASK.value,
                entity_id=created.id,
                action=ActivityAction.TASK_DUPLICATED.value,
                changes=None,
                extra_metadata={
                    "source_task_id": str(source.id),
                    "source_title": source.title,
                    "title": created.title,
                },
            ),
            commit=False,
        )

        self.db.commit()

        full_task = self.repo.get_by_id(created.id, user_id)
        logger.info("Duplicated task id=%s to new_id=%s for user_id=%s", task_id, created.id, user_id)
        return self._to_response(full_task or created)

    def archive_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        task.is_archived = True
        updated = self.repo.update(task, commit=False)

        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=updated.id,
                recurring_task_id=updated.recurring_task_id,
                entity_type=ActivityEntityType.TASK.value,
                entity_id=updated.id,
                action=ActivityAction.TASK_ARCHIVED.value,
                changes={"is_archived": {"old": False, "new": True}},
                extra_metadata={"title": updated.title},
            ),
            commit=False,
        )

        self.db.commit()

        full_task = self.repo.get_by_id(updated.id, user_id)
        return self._to_response(full_task or updated)

    def restore_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        task.is_archived = False
        updated = self.repo.update(task, commit=False)

        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=updated.id,
                recurring_task_id=updated.recurring_task_id,
                entity_type=ActivityEntityType.TASK.value,
                entity_id=updated.id,
                action=ActivityAction.TASK_RESTORED.value,
                changes={"is_archived": {"old": True, "new": False}},
                extra_metadata={"title": updated.title},
            ),
            commit=False,
        )

        self.db.commit()

        full_task = self.repo.get_by_id(updated.id, user_id)
        return self._to_response(full_task or updated)

    def list_tasks(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[TaskPriority] = None,
        category_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        tag_id: Optional[uuid.UUID] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> TaskListResponse:
        """List paginated tasks strictly owned by user_id."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        elif page_size > 100:
            page_size = 100

        valid_sort_fields = {"title", "status", "priority", "due_date", "created_at", "updated_at"}
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        if sort_order.lower() not in ("asc", "desc"):
            sort_order = "desc"

        offset = (page - 1) * page_size
        items, total = self.repo.list_tasks(
            user_id=user_id,
            search=search,
            status=status_filter,
            priority=priority_filter,
            category_id=category_id,
            project_id=project_id,
            tag_id=tag_id,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            is_archived=is_archived,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        response_items = [self._to_response(task) for task in items]

        return TaskListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_statistics(self, user_id: uuid.UUID) -> TaskStatisticsResponse:
        """Calculate task statistics strictly for user_id."""
        stats = self.repo.get_statistics(user_id)
        return TaskStatisticsResponse(**stats)

    # ---------------- Subtasks Management ----------------

    def create_subtask(
        self,
        parent_task_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: SubtaskCreateRequest,
    ) -> SubtaskResponse:
        """Create a subtask under a parent task strictly owned by user_id."""
        parent = self.repo.get_by_id(parent_task_id, user_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent task not found.",
            )

        # Enforce single nesting level: a subtask cannot itself have children
        if parent.parent_task_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot create a subtask under another subtask. Only one nesting level is permitted.",
            )

        now = datetime.now(timezone.utc)
        completed_at = now if payload.status == TaskStatus.COMPLETED else None

        subtask = Task(
            user_id=user_id,
            parent_task_id=parent_task_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=payload.status,
            due_date=payload.due_date,
            completed_at=completed_at,
            is_archived=False,
        )
        created = self.repo.create(subtask, commit=False)
        logger.info("Created subtask id=%s under parent_id=%s for user_id=%s", created.id, parent_task_id, user_id)

        # Log SUBTASK_CREATED
        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=parent_task_id,
                recurring_task_id=parent.recurring_task_id,
                entity_type=ActivityEntityType.SUBTASK.value,
                entity_id=created.id,
                action=ActivityAction.SUBTASK_CREATED.value,
                changes=None,
                extra_metadata={
                    "parent_task_id": str(parent_task_id),
                    "parent_title": parent.title,
                    "title": created.title,
                },
            ),
            commit=False,
        )

        self.db.commit()

        return self._to_subtask_response(created)

    def list_subtasks(self, parent_task_id: uuid.UUID, user_id: uuid.UUID) -> List[SubtaskResponse]:
        """List all subtasks of a parent task strictly owned by user_id."""
        parent = self.repo.get_by_id(parent_task_id, user_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent task not found.",
            )
        subtasks = self.repo.list_subtasks(parent_task_id, user_id)
        return [self._to_subtask_response(st) for st in subtasks]

    def get_subtask(self, subtask_id: uuid.UUID, user_id: uuid.UUID) -> SubtaskResponse:
        """Fetch a single subtask strictly scoped by user_id."""
        subtask = self.repo.get_by_id(subtask_id, user_id)
        if not subtask or subtask.parent_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found.",
            )
        return self._to_subtask_response(subtask)

    def update_subtask(
        self,
        subtask_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: SubtaskUpdateRequest,
    ) -> SubtaskResponse:
        """Update a subtask strictly owned by user_id."""
        subtask = self.repo.get_by_id_for_update(subtask_id, user_id)
        if not subtask or subtask.parent_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found.",
            )

        # Capture diff for subtask
        changes = {}
        old_title = subtask.title
        old_desc = subtask.description
        old_priority = subtask.priority
        old_due = subtask.due_date
        old_status = subtask.status

        if "title" in payload.model_fields_set and payload.title is not None:
            if old_title != payload.title:
                changes["title"] = {"old": old_title, "new": payload.title}
            subtask.title = payload.title
        if "description" in payload.model_fields_set:
            if old_desc != payload.description:
                changes["description"] = {"old": old_desc, "new": payload.description}
            subtask.description = payload.description
        if "priority" in payload.model_fields_set and payload.priority is not None:
            if old_priority != payload.priority:
                changes["priority"] = {
                    "old": old_priority.value if hasattr(old_priority, "value") else str(old_priority),
                    "new": payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
                }
            subtask.priority = payload.priority
        if "due_date" in payload.model_fields_set:
            if old_due != payload.due_date:
                changes["due_date"] = {"old": old_due.isoformat() if old_due else None, "new": payload.due_date.isoformat() if payload.due_date else None}
            subtask.due_date = payload.due_date

        action_type = ActivityAction.SUBTASK_UPDATED
        if "status" in payload.model_fields_set and payload.status is not None:
            new_status = payload.status
            if old_status != new_status:
                changes["status"] = {
                    "old": old_status.value if hasattr(old_status, "value") else str(old_status),
                    "new": new_status.value if hasattr(new_status, "value") else str(new_status),
                }
                if new_status == TaskStatus.COMPLETED:
                    action_type = ActivityAction.SUBTASK_COMPLETED

            subtask.status = new_status
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                subtask.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.COMPLETED and old_status == TaskStatus.COMPLETED:
                subtask.completed_at = None

        updated = self.repo.update(subtask, commit=False)
        logger.info("Updated subtask id=%s for user_id=%s", updated.id, user_id)

        if changes:
            from app.models.activity_log import ActivityLog
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    task_id=subtask.parent_task_id,
                    entity_type=ActivityEntityType.SUBTASK.value,
                    entity_id=updated.id,
                    action=action_type.value,
                    changes=changes,
                    extra_metadata={"title": updated.title, "parent_task_id": str(subtask.parent_task_id)},
                ),
                commit=False,
            )

        self.db.commit()

        return self._to_subtask_response(updated)

    def delete_subtask(self, subtask_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a subtask strictly owned by user_id."""
        subtask = self.repo.get_by_id(subtask_id, user_id)
        if not subtask or subtask.parent_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found.",
            )

        # Log SUBTASK_DELETED
        from app.models.activity_log import ActivityLog
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                task_id=subtask.parent_task_id,
                entity_type=ActivityEntityType.SUBTASK.value,
                entity_id=subtask.id,
                action=ActivityAction.SUBTASK_DELETED.value,
                changes=None,
                extra_metadata={
                    "title": subtask.title,
                    "parent_task_id": str(subtask.parent_task_id),
                },
            ),
            commit=False,
        )

        self.repo.delete(subtask, commit=True)
        logger.info("Deleted subtask id=%s for user_id=%s", subtask_id, user_id)
