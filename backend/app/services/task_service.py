import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatisticsResponse,
    TaskUpdateRequest,
)

logger = logging.getLogger("dayflow.tasks")


class TaskService:
    """Business logic and validation service for task management."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TaskRepository(db)

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

    def _to_response(self, task: Task) -> TaskResponse:
        """Convert a Task model instance into a TaskResponse with dynamic overdue calculation."""
        is_overdue = self._is_task_overdue(task)
        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            start_date=task.start_date,
            due_date=task.due_date,
            completed_at=task.completed_at,
            is_archived=task.is_archived,
            is_overdue=is_overdue,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def create_task(self, user_id: uuid.UUID, payload: TaskCreateRequest) -> TaskResponse:
        """Create a new personal task belonging strictly to user_id."""
        now = datetime.now(timezone.utc)
        completed_at = now if payload.status == TaskStatus.COMPLETED else None

        task = Task(
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            completed_at=completed_at,
            is_archived=False,
        )
        created = self.repo.create(task)
        logger.info("Created task id=%s for user_id=%s", created.id, user_id)
        return self._to_response(created)

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
            # Ensure both are timezone-aware for comparison
            cmp_start = new_start.replace(tzinfo=timezone.utc) if new_start.tzinfo is None else new_start
            cmp_due = new_due.replace(tzinfo=timezone.utc) if new_due.tzinfo is None else new_due
            if cmp_due < cmp_start:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Due date cannot be earlier than start date.",
                )

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
        return self._to_response(updated)

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
        Creates a new task copying title, description, priority, and dates.
        Resets status to TODO, completed_at=None, is_archived=False, fresh UUID and timestamps.
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
            title=duplicated_title,
            description=source.description,
            status=TaskStatus.TODO,
            priority=source.priority,
            start_date=source.start_date,
            due_date=source.due_date,
            completed_at=None,
            is_archived=False,
        )
        created = self.repo.create(new_task)
        logger.info("Duplicated task id=%s to new_id=%s for user_id=%s", task_id, created.id, user_id)
        return self._to_response(created)

    def archive_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        """Mark task as archived."""
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        task.is_archived = True
        updated = self.repo.update(task)
        logger.info("Archived task id=%s for user_id=%s", updated.id, user_id)
        return self._to_response(updated)

    def restore_task(self, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskResponse:
        """Restore archived task to active status."""
        task = self.repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        task.is_archived = False
        updated = self.repo.update(task)
        logger.info("Restored task id=%s for user_id=%s", updated.id, user_id)
        return self._to_response(updated)

    def list_tasks(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[TaskPriority] = None,
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

