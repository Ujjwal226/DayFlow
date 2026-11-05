import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.task import Task, TaskStatus


class ProjectRepository:
    """Database repository for projects strictly isolated per user."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Project]:
        """Fetch a single project strictly filtered by project_id and user_id."""
        stmt = (
            select(Project)
            .where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_for_update(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Project]:
        """Fetch a single project with row-level lock strictly scoped by user_id."""
        stmt = (
            select(Project)
            .where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, project: Project, commit: bool = True) -> Project:
        """Persist a new project in database."""
        self.db.add(project)
        if commit:
            self.db.commit()
            self.db.refresh(project)
        else:
            self.db.flush()
        return project

    def update(self, project: Project, commit: bool = True) -> Project:
        """Save updates to an existing project."""
        project.updated_at = datetime.now(timezone.utc)
        self.db.add(project)
        if commit:
            self.db.commit()
            self.db.refresh(project)
        else:
            self.db.flush()
        return project

    def delete(self, project: Project, commit: bool = True) -> None:
        """
        Delete project record.
        Due to ON DELETE SET NULL on Task.project_id foreign key, tasks are preserved.
        """
        self.db.delete(project)
        if commit:
            self.db.commit()
        else:
            self.db.flush()

    def list_projects(
        self,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        priority: Optional[ProjectPriority] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Project], int]:
        """
        List paginated projects strictly scoped to the authenticated user.
        Supports search by name, status, priority, and archive state.
        """
        query = select(Project).where(
            Project.user_id == user_id,
            Project.is_archived == is_archived,
        )

        if status:
            query = query.where(Project.status == status)

        if priority:
            query = query.where(Project.priority == priority)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                )
            )

        # Count total matching records before pagination
        count_subq = query.subquery()
        count_stmt = select(func.count(count_subq.c.id))
        total = self.db.execute(count_stmt).scalar() or 0

        # Sorting
        sort_column_map = {
            "name": Project.name,
            "status": Project.status,
            "priority": Project.priority,
            "due_date": Project.due_date,
            "created_at": Project.created_at,
            "updated_at": Project.updated_at,
        }
        target_column = sort_column_map.get(sort_by, Project.created_at)

        # Deterministic secondary sorting with Project.id
        if sort_order.lower() == "asc":
            order_clause = [asc(target_column).nulls_last(), asc(Project.id)]
        else:
            order_clause = [desc(target_column).nulls_last(), desc(Project.id)]

        query = (
            query
            .order_by(*order_clause)
            .offset(offset)
            .limit(limit)
        )

        items = list(self.db.execute(query).scalars().all())
        return items, total

    def get_statistics(self, project_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        """
        Efficient SQL aggregation of task counts for a project.
        Excludes subtasks (parent_task_id IS NOT NULL) and archived tasks (is_archived = True).
        """
        now = datetime.now(timezone.utc)

        # Aggregation over active top-level tasks assigned to this project
        stmt = (
            select(
                func.count(Task.id).label("total_tasks"),
                func.count(Task.id).filter(Task.status == TaskStatus.COMPLETED).label("completed_tasks"),
                func.count(Task.id).filter(Task.status == TaskStatus.TODO).label("pending_tasks"),
                func.count(Task.id).filter(Task.status == TaskStatus.IN_PROGRESS).label("in_progress_tasks"),
                func.count(Task.id).filter(Task.status == TaskStatus.CANCELLED).label("cancelled_tasks"),
                func.count(Task.id).filter(
                    and_(
                        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                        Task.due_date.is_not(None),
                        Task.due_date < now,
                    )
                ).label("overdue_tasks"),
            )
            .where(
                Task.project_id == project_id,
                Task.user_id == user_id,
                Task.parent_task_id.is_(None),  # Exclude subtasks
                Task.is_archived.is_(False),     # Exclude archived tasks
            )
        )

        row = self.db.execute(stmt).one()
        total = row.total_tasks or 0
        completed = row.completed_tasks or 0

        # Progress formula: (Completed / Total) * 100, 0 if Total == 0
        if total > 0:
            completion_percentage = round((completed / total) * 100.0, 1)
        else:
            completion_percentage = 0.0

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": row.pending_tasks or 0,
            "in_progress_tasks": row.in_progress_tasks or 0,
            "cancelled_tasks": row.cancelled_tasks or 0,
            "overdue_tasks": row.overdue_tasks or 0,
            "completion_percentage": completion_percentage,
        }

