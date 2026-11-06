import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CalendarEvent(Base):
    """
    Personal calendar event owned strictly by an authenticated user.
    Supports timed events (start_at, end_at) and all-day events (start_date, end_date exclusive).
    """

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    is_all_day: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )

    # Timed event fields (UTC timestamps)
    start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # All-day event fields (Date only, end_date is exclusive)
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="calendar_events")
    task = relationship("Task", backref="calendar_events")

    __table_args__ = (
        Index("ix_calendar_events_user_start_at", "user_id", "start_at"),
        Index("ix_calendar_events_user_start_date", "user_id", "start_date"),
        Index("ix_calendar_events_user_task_id", "user_id", "task_id"),
        CheckConstraint(
            "(is_all_day = false AND start_at IS NOT NULL AND end_at IS NOT NULL AND end_at > start_at AND start_date IS NULL AND end_date IS NULL) OR "
            "(is_all_day = true AND start_date IS NOT NULL AND end_date IS NOT NULL AND end_date > start_date AND start_at IS NULL AND end_at IS NULL)",
            name="ck_calendar_events_valid_representation",
        ),
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, user_id={self.user_id}, title='{self.title[:30]}', is_all_day={self.is_all_day})>"

