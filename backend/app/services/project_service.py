import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest


class ProjectService:
    """Service handling project domain logic, validations, and task associations."""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)

    def create_project(self, user_id: uuid.UUID, payload: ProjectCreateRequest) -> Project:
        """Create a new project for the authenticated user."""
        project = Project(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            color=payload.color or "#3B82F6",
        )
        return self.project_repo.create(project)

    def get_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Retrieve a project strictly belonging to the authenticated user."""
        project = self.project_repo.get_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        return project

    def update_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: ProjectUpdateRequest,
    ) -> Project:
        """
        Update project fields validating date integrity against existing values.
        Uses row-level locking for concurrency safety.
        """
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        # Determine effective dates
        effective_start = payload.start_date if payload.start_date is not None else project.start_date
        effective_due = payload.due_date if payload.due_date is not None else project.due_date

        if effective_start and effective_due and effective_due < effective_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Due date cannot be earlier than start date.",
            )

        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.status is not None:
            project.status = payload.status
        if payload.priority is not None:
            project.priority = payload.priority
        if payload.start_date is not None:
            project.start_date = payload.start_date
        if payload.due_date is not None:
            project.due_date = payload.due_date
        if payload.color is not None:
            project.color = payload.color

        return self.project_repo.update(project)

    def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Delete a project. Associated tasks have project_id set to NULL automatically.
        """
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        self.project_repo.delete(project)

    def archive_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Archive a project."""
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        project.is_archived = True
        return self.project_repo.update(project)

    def restore_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Restore an archived project."""
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        project.is_archived = False
        return self.project_repo.update(project)

    def list_projects(
        self,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        priority: Optional[ProjectPriority] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Project], int]:
        """List paginated projects for user."""
        allowed_sorts = {"name", "status", "priority", "due_date", "created_at", "updated_at"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        return self.project_repo.list_projects(
            user_id=user_id,
            search=search,
            status=status,
            priority=priority,
            is_archived=is_archived,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=page_size,
        )

    def get_project_statistics(self, project_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        """Calculate dynamic project task statistics."""
        # Ensure project exists and belongs to user
        self.get_project(project_id, user_id)
        return self.project_repo.get_statistics(project_id, user_id)

    def assign_task_to_project(
        self,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Task:
        """
        Assign an existing task to a project.
        Both project and task must exist and be owned by the authenticated user.
        Subtasks cannot be independently assigned to projects.
        """
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        task = self.task_repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID '{task_id}' not found.",
            )

        if task.parent_task_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Subtasks cannot be assigned directly to projects.",
            )

        task.project_id = project.id
        return self.task_repo.update(task)

    def remove_task_from_project(
        self,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Task:
        """
        Remove a task from a project.
        """
        # Verify project ownership
        self.get_project(project_id, user_id)

        task = self.task_repo.get_by_id_for_update(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID '{task_id}' not found.",
            )

        if task.project_id == project_id:
            task.project_id = None
            self.task_repo.update(task)

        return task

    def list_project_tasks(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Task], int]:
        """
        List top-level tasks assigned to a specific project.
        """
        # Ensure project exists and belongs to user
        self.get_project(project_id, user_id)

        allowed_sorts = {"title", "status", "priority", "due_date", "created_at", "updated_at"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        if sort_order.lower() not in {"asc", "desc"}:
            sort_order = "desc"

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        return self.task_repo.list_tasks(
            user_id=user_id,
            project_id=project_id,
            search=search,
            status=status,
            priority=priority,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=page_size,
        )
