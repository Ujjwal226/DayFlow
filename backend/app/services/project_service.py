import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest


class ProjectService:
    """Service handling project domain logic, validations, and task associations."""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.activity_repo = ActivityLogRepository(db)

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
        try:
            created = self.project_repo.create(project, commit=False)

            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    entity_type=ActivityEntityType.PROJECT.value,
                    entity_id=created.id,
                    action=ActivityAction.PROJECT_CREATED.value,
                    changes=None,
                    extra_metadata={
                        "name": created.name,
                        "status": created.status.value if hasattr(created.status, "value") else str(created.status),
                        "priority": created.priority.value if hasattr(created.priority, "value") else str(created.priority),
                    },
                ),
                commit=False,
            )

            self.db.commit()
            return created
        except Exception:
            self.db.rollback()
            raise

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

        # Track diff for activity log
        changes = {}
        old_name = project.name
        old_desc = project.description
        old_status = project.status
        old_pri = project.priority
        old_start = project.start_date
        old_due = project.due_date
        old_color = project.color

        if payload.name is not None and payload.name != old_name:
            changes["name"] = {"old": old_name, "new": payload.name}
            project.name = payload.name
        if payload.description is not None and payload.description != old_desc:
            changes["description"] = {"old": old_desc, "new": payload.description}
            project.description = payload.description
        if payload.status is not None and payload.status != old_status:
            changes["status"] = {
                "old": old_status.value if hasattr(old_status, "value") else str(old_status),
                "new": payload.status.value if hasattr(payload.status, "value") else str(payload.status),
            }
            project.status = payload.status
        if payload.priority is not None and payload.priority != old_pri:
            changes["priority"] = {
                "old": old_pri.value if hasattr(old_pri, "value") else str(old_pri),
                "new": payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
            }
            project.priority = payload.priority
        if payload.start_date is not None and payload.start_date != old_start:
            changes["start_date"] = {"old": old_start.isoformat() if old_start else None, "new": payload.start_date.isoformat() if payload.start_date else None}
            project.start_date = payload.start_date
        if payload.due_date is not None and payload.due_date != old_due:
            changes["due_date"] = {"old": old_due.isoformat() if old_due else None, "new": payload.due_date.isoformat() if payload.due_date else None}
            project.due_date = payload.due_date
        if payload.color is not None and payload.color != old_color:
            changes["color"] = {"old": old_color, "new": payload.color}
            project.color = payload.color

        try:
            updated = self.project_repo.update(project, commit=False)

            if changes:
                self.activity_repo.create(
                    ActivityLog(
                        user_id=user_id,
                        actor_id=user_id,
                        entity_type=ActivityEntityType.PROJECT.value,
                        entity_id=updated.id,
                        action=ActivityAction.PROJECT_UPDATED.value,
                        changes=changes,
                        extra_metadata={"name": updated.name},
                    ),
                    commit=False,
                )

            self.db.commit()

            return updated
        except Exception:
            self.db.rollback()
            raise

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

        # Snapshot project before deletion
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                entity_type=ActivityEntityType.PROJECT.value,
                entity_id=project.id,
                action=ActivityAction.PROJECT_DELETED.value,
                changes=None,
                extra_metadata={
                    "name": project.name,
                    "status": project.status.value if hasattr(project.status, "value") else str(project.status),
                },
            ),
            commit=False,
        )

        self.project_repo.delete(project, commit=True)

    def archive_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Archive a project."""
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        project.is_archived = True
        updated = self.project_repo.update(project, commit=False)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                entity_type=ActivityEntityType.PROJECT.value,
                entity_id=updated.id,
                action=ActivityAction.PROJECT_ARCHIVED.value,
                changes={"is_archived": {"old": False, "new": True}},
                extra_metadata={"name": updated.name},
            ),
            commit=False,
        )

        self.db.commit()

        return updated

    def restore_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Restore an archived project."""
        project = self.project_repo.get_by_id_for_update(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        project.is_archived = False
        updated = self.project_repo.update(project, commit=False)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                entity_type=ActivityEntityType.PROJECT.value,
                entity_id=updated.id,
                action=ActivityAction.PROJECT_RESTORED.value,
                changes={"is_archived": {"old": True, "new": False}},
                extra_metadata={"name": updated.name},
            ),
            commit=False,
        )

        self.db.commit()

        return updated

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
