import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session

from app.models.reminder import Notification, NotificationPreference, EmailDelivery


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Notification]:
        query = select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        )
        return self.db.scalars(query).first()

    def list_by_user(
        self,
        user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(query).all())

    def get_unread_count(self, user_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(Notification).where(
            and_(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return self.db.scalar(query) or 0

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read.is_(False)))
            .values(is_read=True, read_at=now)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount

    def delete(self, notification: Notification) -> None:
        self.db.delete(notification)
        self.db.flush()

    # Preference queries
    def get_preference(self, user_id: uuid.UUID) -> Optional[NotificationPreference]:
        query = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        return self.db.scalars(query).first()

    def create_preference(self, pref: NotificationPreference) -> NotificationPreference:
        self.db.add(pref)
        self.db.flush()
        self.db.refresh(pref)
        return pref

    def update_preference(self, pref: NotificationPreference) -> NotificationPreference:
        self.db.flush()
        self.db.refresh(pref)
        return pref

    # Email delivery queries
    def create_email_delivery(self, delivery: EmailDelivery) -> EmailDelivery:
        self.db.add(delivery)
        self.db.flush()
        self.db.refresh(delivery)
        return delivery

    def get_pending_email_deliveries(
        self, current_time: datetime, limit: int = 50, lock: bool = False
    ) -> List[EmailDelivery]:
        query = select(EmailDelivery).where(
            and_(
                EmailDelivery.status == "PENDING",
                EmailDelivery.next_retry_at <= current_time,
            )
        ).order_by(EmailDelivery.created_at.asc()).limit(limit)

        if lock:
            bind = self.db.get_bind()
            if bind and bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            elif bind and bind.dialect.name != "sqlite":
                query = query.with_for_update()

        return list(self.db.scalars(query).all())

    def update_email_delivery(self, delivery: EmailDelivery) -> EmailDelivery:
        self.db.flush()
        self.db.refresh(delivery)
        return delivery
