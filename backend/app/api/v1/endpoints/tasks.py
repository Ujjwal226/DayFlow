import enum
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.task import (
    SubtaskCreateRequest,
    SubtaskResponse,
    TaskCategoryAssignmentRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatisticsResponse,
    TaskTagsAssignmentRequest,
    TaskUpdateRequest,
)
from app.services.task_service import TaskService


class TaskSortField(str, enum.Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    STATUS = "status"
    TITLE = "title"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Create a task owned strictly by the authenticated user."""
    service = TaskService(db)
    return service.create_task(user_id=current_user.id, payload=payload)


@router.get(
    "",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated tasks with filters",
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query in title or description"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project ID"),
    tag_id: Optional[uuid.UUID] = Query(None, description="Filter by tag ID"),
    due_date_from: Optional[datetime] = Query(None, description="Filter by minimum due date"),
    due_date_to: Optional[datetime] = Query(None, description="Filter by maximum due date"),
    is_archived: bool = Query(False, description="Filter archived vs active tasks"),
    sort_by: TaskSortField = Query(TaskSortField.CREATED_AT, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort direction: asc or desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """List tasks owned strictly by the authenticated user with search and filtering."""
    service = TaskService(db)
    return service.list_tasks(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        priority_filter=priority,
        category_id=category_id,
        project_id=project_id,
        tag_id=tag_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        is_archived=is_archived,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )


@router.get(
    "/statistics",
    response_model=TaskStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated task statistics",
)
def get_task_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskStatisticsResponse:
    """Calculate aggregated task counts and overdue metrics for the authenticated user."""
    service = TaskService(db)
    return service.get_statistics(user_id=current_user.id)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single task",
)
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Retrieve task details strictly scoped to current user."""
    service = TaskService(db)
    return service.get_task(user_id=current_user.id, task_id=task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task partially",
)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Update fields on a user-owned task."""
    service = TaskService(db)
    return service.update_task(user_id=current_user.id, task_id=task_id, payload=payload)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete task",
)
def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Delete a user-owned task."""
    service = TaskService(db)
    service.delete_task(user_id=current_user.id, task_id=task_id)
    return MessageResponse(status="ok", message="Task deleted successfully.")


@router.post(
    "/{task_id}/duplicate",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate an existing task",
)
def duplicate_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Duplicate a user's task with fresh UUID and TODO status."""
    service = TaskService(db)
    return service.duplicate_task(user_id=current_user.id, task_id=task_id)


@router.patch(
    "/{task_id}/archive",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive task",
)
def archive_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Archive a user-owned task."""
    service = TaskService(db)
    return service.archive_task(user_id=current_user.id, task_id=task_id)


@router.patch(
    "/{task_id}/restore",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore an archived task",
)
def restore_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Restore an archived task to active state."""
    service = TaskService(db)
    return service.restore_task(user_id=current_user.id, task_id=task_id)


# ---------------- Category & Tag Assignment Endpoints ----------------

@router.patch(
    "/{task_id}/category",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign or remove category for a task",
)
def assign_task_category(
    task_id: uuid.UUID,
    payload: TaskCategoryAssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Assign or remove category for task, strictly validating user ownership."""
    service = TaskService(db)
    return service.assign_category(user_id=current_user.id, task_id=task_id, payload=payload)


@router.put(
    "/{task_id}/tags",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace assigned tags for a task",
)
def assign_task_tags(
    task_id: uuid.UUID,
    payload: TaskTagsAssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Replace all tags assigned to a task, strictly validating user ownership."""
    service = TaskService(db)
    return service.assign_tags(user_id=current_user.id, task_id=task_id, payload=payload)


# ---------------- Subtasks Endpoints on Parent Task ----------------

@router.post(
    "/{task_id}/subtasks",
    response_model=SubtaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subtask under a parent task",
)
def create_subtask(
    task_id: uuid.UUID,
    payload: SubtaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskResponse:
    """Create a subtask under the specified parent task."""
    service = TaskService(db)
    return service.create_subtask(parent_task_id=task_id, user_id=current_user.id, payload=payload)


@router.get(
    "/{task_id}/subtasks",
    response_model=List[SubtaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List subtasks under a parent task",
)
def list_subtasks(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SubtaskResponse]:
    """List subtasks belonging to a parent task."""
    service = TaskService(db)
    return service.list_subtasks(parent_task_id=task_id, user_id=current_user.id)
