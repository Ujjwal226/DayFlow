import enum
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.task import TaskPriority


class RecurrenceFrequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class RecurringTask(Base):
    """Recurring Task series rule/template owned strictly by an authenticated user."""

    __tablename__ = "recurring_tasks"

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

    # Template task properties
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority"),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Recurrence rules
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency, name="recurrence_frequency"),
        nullable=False,
        index=True,
    )
    interval: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    max_occurrences: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Recurrence specifics
    # weekdays: list of integer weekdays (0=Monday, 6=Sunday) stored as JSON or string
    weekdays: Mapped[Optional[str]] = mapped_column(
        String(50),  # e.g., "0,4" for Mon & Fri
        nullable=True,
    )
    day_of_month: Mapped[Optional[int]] = mapped_column(
        Integer,  # 1-31, or -1 for last day of month
        nullable=True,
    )
    month_of_year: Mapped[Optional[int]] = mapped_column(
        Integer,  # 1-12 for yearly recurrence
        nullable=True,
    )
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="UTC",
    )

    # Generation tracking
    next_occurrence_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    occurrences_generated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Lifecycle state: True=ACTIVE, False=PAUSED/STOPPED
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    is_stopped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    user = relationship("User", backref="recurring_tasks")
    category = relationship("Category")
    project = relationship("Project")
    occurrences = relationship("Task", back_populates="recurring_task", cascade="all, delete-orphan")
    skipped_occurrences = relationship("RecurringTaskSkip", back_populates="recurring_task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_recurring_tasks_user_active_next", "user_id", "is_active", "is_stopped", "next_occurrence_date"),
    )

    def __repr__(self) -> str:
        return f"<RecurringTask(id={self.id}, user_id={self.user_id}, title='{self.title[:30]}', freq='{self.frequency}')>"


class RecurringTaskSkip(Base):
    """Explicitly skipped dates for a recurring task series."""

    __tablename__ = "recurring_task_skips"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    recurring_task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recurring_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skip_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    recurring_task = relationship("RecurringTask", back_populates="skipped_occurrences")

    __table_args__ = (
        UniqueConstraint("recurring_task_id", "skip_date", name="uq_recurring_task_skips_task_date"),
        Index("ix_recurring_task_skips_task_date", "recurring_task_id", "skip_date"),
    )

