import math
import uuid
from datetime import date, datetime
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.calendar_event import CalendarEvent
from app.models.task import Task


class CalendarEventRepository:
    """Database repository for personal calendar events strictly isolated per user."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CalendarEvent]:
        """Fetch a single calendar event strictly scoped by event_id and user_id."""
        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.task))
            .where(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_for_update(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CalendarEvent]:
        """Fetch a single calendar event with row-level lock strictly scoped by user_id."""
        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.task))
            .where(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id,
            )
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, event: CalendarEvent, commit: bool = True) -> CalendarEvent:
        """Persist a new calendar event."""
        self.db.add(event)
        if commit:
            self.db.commit()
            self.db.refresh(event)
        else:
            self.db.flush()
        return event

    def update(self, event: CalendarEvent, commit: bool = True) -> CalendarEvent:
        """Save updates to an existing calendar event."""
        self.db.add(event)
        if commit:
            self.db.commit()
            self.db.refresh(event)
        else:
            self.db.flush()
        return event

    def delete(self, event: CalendarEvent, commit: bool = True) -> None:
        """Delete calendar event record."""
        self.db.delete(event)
        if commit:
            self.db.commit()
        else:
            self.db.flush()

    def list_events(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CalendarEvent], int]:
        """List paginated calendar events strictly scoped to user."""
        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.task))
            .where(CalendarEvent.user_id == user_id)
            .order_by(desc(CalendarEvent.created_at), desc(CalendarEvent.id))
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.execute(stmt).scalars().all())

        count_stmt = select(func.count(CalendarEvent.id)).where(CalendarEvent.user_id == user_id)
        total = self.db.execute(count_stmt).scalar() or 0

        return items, total

    def list_by_task_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> List[CalendarEvent]:
        """List all calendar events associated with a specific task."""
        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.task_id == task_id,
                CalendarEvent.user_id == user_id,
            )
            .order_by(CalendarEvent.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_events_for_range(
        self,
        user_id: uuid.UUID,
        range_start_utc: datetime,
        range_end_utc: datetime,
        local_start_date: date,
        local_end_date: date,
    ) -> List[CalendarEvent]:
        """
        Retrieve all calendar events overlapping the requested range.
        - Timed events: event.start_at < range_end_utc AND event.end_at > range_start_utc
        - All-day events: event.start_date < local_end_date AND event.end_date > local_start_date
        """
        timed_condition = and_(
            CalendarEvent.is_all_day == False,  # noqa: E712
            CalendarEvent.start_at < range_end_utc,
            CalendarEvent.end_at > range_start_utc,
        )

        allday_condition = and_(
            CalendarEvent.is_all_day == True,  # noqa: E712
            CalendarEvent.start_date < local_end_date,
            CalendarEvent.end_date > local_start_date,
        )

        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.task))
            .where(
                CalendarEvent.user_id == user_id,
                or_(timed_condition, allday_condition),
            )
            .order_by(
                CalendarEvent.start_at.asc().nulls_last(),
                CalendarEvent.start_date.asc().nulls_last(),
                CalendarEvent.id.asc(),
            )
        )
        return list(self.db.execute(stmt).scalars().all())
