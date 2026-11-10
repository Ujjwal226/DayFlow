import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reminder import Notification, NotificationPreference
from app.repositories.notification_repository import NotificationRepository
from app.schemas.reminder import (
    NotificationCreate,
    NotificationPreferenceUpdate,
)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def get_notification(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = self.repo.get_by_id(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        return notification

    def list_notifications(
        self,
        user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        return self.repo.list_by_user(user_id=user_id, is_read=is_read, limit=limit, offset=offset)

    def get_unread_count(self, user_id: uuid.UUID) -> int:
        return self.repo.get_unread_count(user_id)

    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = self.get_notification(notification_id, user_id)
        updated = self.repo.mark_as_read(notification)
        self.db.commit()
        return updated

    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        count = self.repo.mark_all_as_read(user_id)
        self.db.commit()
        return count

    def delete_notification(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        notification = self.get_notification(notification_id, user_id)
        self.repo.delete(notification)
        self.db.commit()

    def get_or_create_preferences(self, user_id: uuid.UUID) -> NotificationPreference:
        pref = self.repo.get_preference(user_id)
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                in_app_enabled=True,
                email_enabled=True,
                task_reminders_enabled=True,
                due_date_reminders_enabled=True,
                overdue_reminders_enabled=True,
                preferred_timezone="UTC",
                quiet_hours_enabled=False,
            )
            pref = self.repo.create_preference(pref)
            self.db.commit()
        return pref

    def update_preferences(self, user_id: uuid.UUID, data: NotificationPreferenceUpdate) -> NotificationPreference:
        pref = self.get_or_create_preferences(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pref, field, value)
        updated = self.repo.update_preference(pref)
        self.db.commit()
        return updated

