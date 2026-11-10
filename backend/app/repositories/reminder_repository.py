import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Reminder]:
        query = select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        return self.db.scalars(query).first()

    def list_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Reminder]:
        query = select(Reminder).where(Reminder.user_id == user_id)
        if status:
            query = query.where(Reminder.status == status)
        if task_id:
            query = query.where(Reminder.task_id == task_id)
        query = query.order_by(Reminder.scheduled_at.asc()).offset(offset).limit(limit)
        return list(self.db.scalars(query).all())

    def create(self, reminder: Reminder) -> Reminder:
        self.db.add(reminder)
        self.db.flush()
        self.db.refresh(reminder)
        return reminder

    def update(self, reminder: Reminder) -> Reminder:
        self.db.flush()
        self.db.refresh(reminder)
        return reminder

    def delete(self, reminder: Reminder) -> None:
        self.db.delete(reminder)
        self.db.flush()

    def get_due_reminders(self, current_time: datetime, limit: int = 50, lock: bool = False) -> List[Reminder]:
        """Find pending or snoozed reminders whose scheduled/snoozed time <= current_time.
        
        When lock=True, applies FOR UPDATE SKIP LOCKED if supported (PostgreSQL).
        """
        query = select(Reminder).where(
            or_(
                and_(Reminder.status == "PENDING", Reminder.scheduled_at <= current_time),
                and_(Reminder.status == "SNOOZED", Reminder.snoozed_until <= current_time),
            )
        ).order_by(Reminder.scheduled_at.asc()).limit(limit)

        if lock:
            # Check if dialect supports FOR UPDATE SKIP LOCKED
            bind = self.db.get_bind()
            if bind and bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            elif bind and bind.dialect.name != "sqlite":
                query = query.with_for_update()

        return list(self.db.scalars(query).all())
