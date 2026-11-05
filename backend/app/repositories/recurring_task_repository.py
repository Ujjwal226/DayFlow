import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.recurring_task import RecurrenceFrequency, RecurringTask, RecurringTaskSkip
from app.models.task import Task


class RecurringTaskRepository:
    """Repository for managing recurring task templates and skips with strict user scoping."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, series_id: uuid.UUID, user_id: uuid.UUID) -> Optional[RecurringTask]:
        stmt = (
            select(RecurringTask)
            .options(
                selectinload(RecurringTask.category),
                selectinload(RecurringTask.project),
            )
            .where(
                RecurringTask.id == series_id,
                RecurringTask.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_for_update(self, series_id: uuid.UUID, user_id: uuid.UUID) -> Optional[RecurringTask]:
        stmt = (
            select(RecurringTask)
            .options(
                selectinload(RecurringTask.category),
                selectinload(RecurringTask.project),
            )
            .where(
                RecurringTask.id == series_id,
                RecurringTask.user_id == user_id,
            )
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, series: RecurringTask, commit: bool = False) -> RecurringTask:
        self.db.add(series)
        if commit:
            self.db.commit()
            self.db.refresh(series)
        else:
            self.db.flush()
        return series

    def update(self, series: RecurringTask, commit: bool = False) -> RecurringTask:
        series.updated_at = datetime.now(timezone.utc)
        self.db.add(series)
        if commit:
            self.db.commit()
            self.db.refresh(series)
        else:
            self.db.flush()
        return series

    def delete(self, series: RecurringTask, commit: bool = False) -> None:
        self.db.delete(series)
        if commit:
            self.db.commit()
        else:
            self.db.flush()

    def list_series(
        self,
        user_id: uuid.UUID,
        frequency: Optional[RecurrenceFrequency] = None,
        is_active: Optional[bool] = None,
        is_stopped: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[RecurringTask], int]:
        query = select(RecurringTask).where(RecurringTask.user_id == user_id)

        if frequency:
            query = query.where(RecurringTask.frequency == frequency)
        if is_active is not None:
            query = query.where(RecurringTask.is_active == is_active)
        if is_stopped is not None:
            query = query.where(RecurringTask.is_stopped == is_stopped)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    RecurringTask.title.ilike(pattern),
                    RecurringTask.description.ilike(pattern),
                )
            )

        count_subq = query.subquery()
        count_stmt = select(func.count(count_subq.c.id))
        total = self.db.execute(count_stmt).scalar() or 0

        query = (
            query.options(
                selectinload(RecurringTask.category),
                selectinload(RecurringTask.project),
            )
            .order_by(desc(RecurringTask.created_at), desc(RecurringTask.id))
            .offset(offset)
            .limit(limit)
        )

        items = list(self.db.execute(query).scalars().all())
        return items, total

    def add_skip(self, skip: RecurringTaskSkip, commit: bool = False) -> RecurringTaskSkip:
        self.db.add(skip)
        if commit:
            self.db.commit()
            self.db.refresh(skip)
        else:
            self.db.flush()
        return skip

    def is_date_skipped(self, series_id: uuid.UUID, target_date: date) -> bool:
        stmt = select(RecurringTaskSkip).where(
            RecurringTaskSkip.recurring_task_id == series_id,
            RecurringTaskSkip.skip_date == target_date,
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def get_due_series_for_generation(self, cutoff_date: date, user_id: Optional[uuid.UUID] = None) -> List[RecurringTask]:
        """Fetch active, unstopped series whose next_occurrence_date <= cutoff_date."""
        query = select(RecurringTask).where(
            RecurringTask.is_active.is_(True),
            RecurringTask.is_stopped.is_(False),
            RecurringTask.next_occurrence_date.is_not(None),
            RecurringTask.next_occurrence_date <= cutoff_date,
        )
        if user_id:
            query = query.where(RecurringTask.user_id == user_id)

        return list(self.db.execute(query).scalars().all())

