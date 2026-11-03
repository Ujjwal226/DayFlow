import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.tag import Tag, TaskTag
from app.models.task import Task, TaskPriority, TaskStatus


class TaskRepository:
    """Database repository for personal tasks strictly isolated per user."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Task]:
        """Fetch a single task strictly filtered by task_id and user_id, loading relations."""
        stmt = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.tags),
                selectinload(Task.subtasks),
            )
            .where(
                Task.id == task_id,
                Task.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_for_update(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Task]:
        """Fetch a single task with row-level lock strictly scoped by user_id."""
        stmt = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.tags),
                selectinload(Task.subtasks),
            )
            .where(
                Task.id == task_id,
                Task.user_id == user_id,
            )
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, task: Task) -> Task:
        """Persist a new task in database."""
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task: Task) -> Task:
        """Save updates to an existing task."""
        task.updated_at = datetime.now(timezone.utc)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """Delete task record."""
        self.db.delete(task)
        self.db.commit()

    def list_subtasks(self, parent_task_id: uuid.UUID, user_id: uuid.UUID) -> List[Task]:
        """List subtasks belonging to a parent task strictly scoped by user_id."""
        stmt = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.tags),
            )
            .where(
                Task.parent_task_id == parent_task_id,
                Task.user_id == user_id,
            )
            .order_by(Task.created_at.asc(), Task.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_tasks(
        self,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        category_id: Optional[uuid.UUID] = None,
        tag_id: Optional[uuid.UUID] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        """
        List paginated top-level tasks strictly scoped to the authenticated user.
        Supports search, filtering by status, priority, category, tag, due date range, and archiving.
        Excludes subtasks (parent_task_id IS NOT NULL) so they do not clutter top-level task views.
        """
        query = select(Task).where(
            Task.user_id == user_id,
            Task.is_archived == is_archived,
            Task.parent_task_id.is_(None),  # Top-level tasks only
        )

        # Category filter
        if category_id:
            query = query.where(Task.category_id == category_id)

        # Tag filter (join task_tags association table with distinct to prevent duplicates)
        if tag_id:
            query = query.join(TaskTag, TaskTag.task_id == Task.id).where(TaskTag.tag_id == tag_id)

        # Status filter
        if status:
            query = query.where(Task.status == status)

        # Priority filter
        if priority:
            query = query.where(Task.priority == priority)

        # Due date range filter
        if due_date_from:
            query = query.where(Task.due_date >= due_date_from)
        if due_date_to:
            query = query.where(Task.due_date <= due_date_to)

        # Search filter (case-insensitive in title or description)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern),
                )
            )

        # Count total matching records before pagination
        count_subq = query.subquery()
        count_stmt = select(func.count(func.distinct(count_subq.c.id)))
        total = self.db.execute(count_stmt).scalar() or 0

        # Sorting
        sort_column_map = {
            "title": Task.title,
            "status": Task.status,
            "priority": Task.priority,
            "due_date": Task.due_date,
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
        }
        target_column = sort_column_map.get(sort_by, Task.created_at)
        # Deterministic sorting: append Task.id as a tie-breaker
        if sort_order.lower() == "asc":
            # For ascending due_date sort, put nulls last so upcoming tasks appear first
            order_clause = [asc(target_column).nulls_last(), asc(Task.id)]
        else:
            order_clause = [desc(target_column).nulls_last(), desc(Task.id)]

        query = (
            query.options(
                selectinload(Task.category),
                selectinload(Task.tags),
                selectinload(Task.subtasks),
            )
            .order_by(*order_clause)
            .offset(offset)
            .limit(limit)
        )

        items = list(self.db.execute(query).scalars().all())
        return items, total

    def list_tasks_by_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        """Fetch tasks belonging to a specific category."""
        return self.list_tasks(
            user_id=user_id,
            category_id=category_id,
            offset=offset,
            limit=limit,
        )

    def get_statistics(
        self,
        user_id: uuid.UUID,
        upcoming_window_days: int = 7,
        now: Optional[datetime] = None,
    ) -> dict:
        """
        Calculate aggregated task statistics strictly scoped to user_id.
        Excludes archived tasks and subtasks from active statistics.
        Calculates counts using efficient database aggregation functions.
        Upcoming tasks are defined as non-completed, non-cancelled tasks with:
            now <= due_date <= now + upcoming_window_days
        """
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        upcoming_cutoff = current_time + timedelta(days=upcoming_window_days)

        # Base filter for active (non-archived) user tasks (top-level)
        base_filter = and_(
            Task.user_id == user_id,
            Task.is_archived.is_(False),
            Task.parent_task_id.is_(None),
        )

        # Incomplete filter for overdue and upcoming
        incomplete_filter = and_(
            base_filter,
            Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
            Task.due_date.isnot(None),
        )

        stmt = select(
            func.count(Task.id).label("total"),
            func.count(func.nullif(Task.status == TaskStatus.TODO, False)).label("todo"),
            func.count(func.nullif(Task.status == TaskStatus.IN_PROGRESS, False)).label("in_progress"),
            func.count(func.nullif(Task.status == TaskStatus.COMPLETED, False)).label("completed"),
            func.count(func.nullif(Task.status == TaskStatus.CANCELLED, False)).label("cancelled"),
        ).where(base_filter)

        row = self.db.execute(stmt).one()

        # Overdue count: incomplete tasks with due_date < current_time
        overdue_stmt = select(func.count(Task.id)).where(
            incomplete_filter,
            Task.due_date < current_time,
        )
        overdue_count = self.db.execute(overdue_stmt).scalar() or 0

        # Upcoming count: incomplete tasks with current_time <= due_date <= upcoming_cutoff (7-day window)
        upcoming_stmt = select(func.count(Task.id)).where(
            incomplete_filter,
            Task.due_date >= current_time,
            Task.due_date <= upcoming_cutoff,
        )
        upcoming_count = self.db.execute(upcoming_stmt).scalar() or 0

        return {
            "total": row.total or 0,
            "todo": row.todo or 0,
            "in_progress": row.in_progress or 0,
            "completed": row.completed or 0,
            "cancelled": row.cancelled or 0,
            "overdue": overdue_count,
            "upcoming": upcoming_count,
        }
