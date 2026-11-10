import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.models.task import Task
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderSnooze


class ReminderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReminderRepository(db)

    def _validate_task(self, task_id: Optional[uuid.UUID], user_id: uuid.UUID) -> None:
        if task_id:
            task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated task not found or does not belong to you",
                )

    def create_reminder(self, user_id: uuid.UUID, data: ReminderCreate) -> Reminder:
        self._validate_task(data.task_id, user_id)
        
        # Ensure scheduled_at is timezone-aware
        scheduled_at = data.scheduled_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        reminder = Reminder(
            user_id=user_id,
            task_id=data.task_id,
            title=data.title,
            description=data.description,
            scheduled_at=scheduled_at,
            timezone=data.timezone,
            recurrence=data.recurrence,
            delivery_channels=data.delivery_channels,
            status="PENDING",
        )
        created = self.repo.create(reminder)
        self.db.commit()
        return created

    def get_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
        reminder = self.repo.get_by_id(reminder_id, user_id)
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found",
            )
        return reminder

    def list_reminders(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Reminder]:
        return self.repo.list_by_user(
            user_id=user_id,
            status=status_filter,
            task_id=task_id,
            limit=limit,
            offset=offset,
        )

    def update_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID, data: ReminderUpdate) -> Reminder:
        reminder = self.get_reminder(reminder_id, user_id)
        update_data = data.model_dump(exclude_unset=True)

        if "task_id" in update_data and update_data["task_id"] is not None:
            self._validate_task(update_data["task_id"], user_id)

        if "scheduled_at" in update_data and update_data["scheduled_at"] is not None:
            sched = update_data["scheduled_at"]
            if sched.tzinfo is None:
                update_data["scheduled_at"] = sched.replace(tzinfo=timezone.utc)

        for field, value in update_data.items():
            setattr(reminder, field, value)

        updated = self.repo.update(reminder)
        self.db.commit()
        return updated

    def snooze_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID, data: ReminderSnooze) -> Reminder:
        reminder = self.get_reminder(reminder_id, user_id)
        now = datetime.now(timezone.utc)
        snooze_until = now + timedelta(minutes=data.snooze_minutes)

        reminder.status = "SNOOZED"
        reminder.snoozed_until = snooze_until

        updated = self.repo.update(reminder)
        self.db.commit()
        return updated

    def complete_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
        reminder = self.get_reminder(reminder_id, user_id)
        reminder.status = "COMPLETED"
        reminder.snoozed_until = None
        updated = self.repo.update(reminder)
        self.db.commit()
        return updated

    def dismiss_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
        reminder = self.get_reminder(reminder_id, user_id)
        reminder.status = "DISMISSED"
        reminder.snoozed_until = None
        updated = self.repo.update(reminder)
        self.db.commit()
        return updated

    def delete_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        reminder = self.get_reminder(reminder_id, user_id)
        self.repo.delete(reminder)
        self.db.commit()

