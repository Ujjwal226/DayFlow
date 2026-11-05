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
        created = self.repo.create(task)
        logger.info("Created task id=%s for user_id=%s", created.id, user_id)
        # Re-fetch with relations loaded
        full_task = self.repo.get_by_id(created.id, user_id)
        return self._to_response(full_task or created)

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

        # Validate tag ownership if updating tags
        if "tag_ids" in payload.model_fields_set and payload.tag_ids is not None:
            tags = self.tag_repo.get_by_ids(payload.tag_ids, user_id)
            if len(tags) != len(set(payload.tag_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tags not found.",
                )
            task.tags = tags

        if "title" in payload.model_fields_set and payload.title is not None:
            task.title = payload.title
        if "description" in payload.model_fields_set:
            task.description = payload.description
        if "priority" in payload.model_fields_set and payload.priority is not None:
            task.priority = payload.priority
        if "start_date" in payload.model_fields_set:
            task.start_date = payload.start_date
        if "due_date" in payload.model_fields_set:
            task.due_date = payload.due_date

        if "status" in payload.model_fields_set and payload.status is not None:
            old_status = task.status
            new_status = payload.status
            task.status = new_status
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                task.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.COMPLETED and old_status == TaskStatus.COMPLETED:
                task.completed_at = None

        updated = self.repo.update(task)
        logger.info("Updated task id=%s for user_id=%s", updated.id, user_id)
        full_task = self.repo.get_by_id(updated.id, user_id)
        return self._to_response(full_task or updated)

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

        updated = self.repo.update(task)
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

        task.tags = tags
        updated = self.repo.update(task)
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
        self.repo.delete(task)
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
        created = self.repo.create(new_task)
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
        updated = self.repo.update(task)
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
        updated = self.repo.update(task)
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
        created = self.repo.create(subtask)
        logger.info("Created subtask id=%s under parent_id=%s for user_id=%s", created.id, parent_task_id, user_id)
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

        if "title" in payload.model_fields_set and payload.title is not None:
            subtask.title = payload.title
        if "description" in payload.model_fields_set:
            subtask.description = payload.description
        if "priority" in payload.model_fields_set and payload.priority is not None:
            subtask.priority = payload.priority
        if "due_date" in payload.model_fields_set:
            subtask.due_date = payload.due_date

        if "status" in payload.model_fields_set and payload.status is not None:
            old_status = subtask.status
            new_status = payload.status
            subtask.status = new_status
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                subtask.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.COMPLETED and old_status == TaskStatus.COMPLETED:
                subtask.completed_at = None

        updated = self.repo.update(subtask)
        logger.info("Updated subtask id=%s for user_id=%s", updated.id, user_id)
        return self._to_subtask_response(updated)

    def delete_subtask(self, subtask_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a subtask strictly owned by user_id."""
        subtask = self.repo.get_by_id(subtask_id, user_id)
        if not subtask or subtask.parent_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found.",
            )
        self.repo.delete(subtask)
        logger.info("Deleted subtask id=%s for user_id=%s", subtask_id, user_id)
