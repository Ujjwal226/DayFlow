import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.project import ProjectPriority, ProjectStatus
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatisticsResponse,
    ProjectUpdateRequest,
)
from app.schemas.task import TaskListResponse, TaskResponse
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a new project for the authenticated user."""
    service = ProjectService(db)
    project = service.create_project(current_user.id, payload)
    stats = service.get_project_statistics(project.id, current_user.id)
    resp = ProjectResponse.model_validate(project)
    resp.statistics = ProjectStatisticsResponse(**stats)
    return resp


@router.get("", response_model=ProjectListResponse)
def list_projects(
    search: Optional[str] = Query(None, description="Search project name or description"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    priority: Optional[ProjectPriority] = Query(None, description="Filter by project priority"),
    is_archived: bool = Query(False, description="Filter by archived state"),
    sort_by: str = Query("created_at", description="Sort field: name, status, priority, due_date, created_at, updated_at"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    """List paginated projects owned by the authenticated user."""
    service = ProjectService(db)
    items, total = service.list_projects(
        user_id=current_user.id,
        search=search,
        status=status,
        priority=priority,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    project_responses = []
    for item in items:
        resp = ProjectResponse.model_validate(item)
        stats = service.get_project_statistics(item.id, current_user.id)
        resp.statistics = ProjectStatisticsResponse(**stats)
        project_responses.append(resp)

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ProjectListResponse(
        items=project_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Retrieve a project by UUID for authenticated user."""
    service = ProjectService(db)
    project = service.get_project(project_id, current_user.id)
    stats = service.get_project_statistics(project.id, current_user.id)
    resp = ProjectResponse.model_validate(project)
    resp.statistics = ProjectStatisticsResponse(**stats)
    return resp


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Partially update a project."""
    service = ProjectService(db)
    project = service.update_project(project_id, current_user.id, payload)
    stats = service.get_project_statistics(project.id, current_user.id)
    resp = ProjectResponse.model_validate(project)
    resp.statistics = ProjectStatisticsResponse(**stats)
    return resp


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a project while preserving its associated tasks."""
    service = ProjectService(db)
    service.delete_project(project_id, current_user.id)


@router.patch("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Archive a project."""
    service = ProjectService(db)
    project = service.archive_project(project_id, current_user.id)
    stats = service.get_project_statistics(project.id, current_user.id)
    resp = ProjectResponse.model_validate(project)
    resp.statistics = ProjectStatisticsResponse(**stats)
    return resp


@router.patch("/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Restore an archived project."""
    service = ProjectService(db)
    project = service.restore_project(project_id, current_user.id)
    stats = service.get_project_statistics(project.id, current_user.id)
    resp = ProjectResponse.model_validate(project)
    resp.statistics = ProjectStatisticsResponse(**stats)
    return resp


@router.get("/{project_id}/statistics", response_model=ProjectStatisticsResponse)
def get_project_statistics(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectStatisticsResponse:
    """Get dynamically calculated project statistics."""
    service = ProjectService(db)
    stats = service.get_project_statistics(project_id, current_user.id)
    return ProjectStatisticsResponse(**stats)


@router.get("/{project_id}/tasks", response_model=TaskListResponse)
def list_project_tasks(
    project_id: uuid.UUID,
    search: Optional[str] = Query(None, description="Search task title or description"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    sort_by: str = Query("created_at", description="Sort field: title, status, priority, due_date, created_at, updated_at"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """List tasks assigned to a project."""
    service = ProjectService(db)
    task_service = TaskService(db)
    items, total = service.list_project_tasks(
        project_id=project_id,
        user_id=current_user.id,
        search=search,
        status=status,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    task_responses = [task_service._to_response(item) for item in items]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return TaskListResponse(
        items=task_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.put("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def assign_task_to_project(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Assign an existing task to a project."""
    service = ProjectService(db)
    task_service = TaskService(db)
    task = service.assign_task_to_project(project_id, task_id, current_user.id)
    full_task = task_service.repo.get_by_id(task.id, current_user.id)
    return task_service._to_response(full_task or task)


@router.delete("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def remove_task_from_project(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Remove a task from a project."""
    service = ProjectService(db)
    task_service = TaskService(db)
    task = service.remove_task_from_project(project_id, task_id, current_user.id)
    full_task = task_service.repo.get_by_id(task.id, current_user.id)
    return task_service._to_response(full_task or task)
