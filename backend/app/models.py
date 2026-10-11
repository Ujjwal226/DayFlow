"""
DayFlow backend – SQLAlchemy ORM models.

Design notes
------------
* All UTC timestamps use ``datetime`` with tzinfo so SQLAlchemy / SQLite
  store an ISO-8601 string that is unambiguously UTC.
* scheduled_date / start_time / end_time are local calendar values for
  Asia/Kolkata – stored as plain date / time columns without tz conversion.
* Soft deletion: tasks are never physically removed; deleted_at is set
  instead.
* TaskEvent is scaffolded for future history tracking but not wired to
  any endpoint in Stage 1.
"""
from __future__ import annotations

import enum
from datetime import date, datetime, time, timezone

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #

class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Category(str, enum.Enum):
    work = "work"
    personal = "personal"
    learning = "learning"
    health = "health"
    other = "other"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"


class EventType(str, enum.Enum):
    created = "created"
    updated = "updated"
    completed = "completed"
    reopened = "reopened"
    deleted = "deleted"
    rescheduled = "rescheduled"


# --------------------------------------------------------------------------- #
# Task
# --------------------------------------------------------------------------- #

class Task(Base):
    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Calendar scheduling (local Asia/Kolkata values – no tz conversion)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Classification
    priority: Mapped[str] = mapped_column(
        SAEnum(Priority, name="priority_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Priority.medium.value,
    )
    category: Mapped[str] = mapped_column(
        SAEnum(Category, name="category_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Category.other.value,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(TaskStatus, name="task_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskStatus.pending.value,
        index=True,
    )

    # Timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # History: preserve original planned date for rescheduling tracking
    original_scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationship to history events
    events: Mapped[list["TaskEvent"]] = relationship(
        "TaskEvent",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id!r} title={self.title!r} status={self.status!r}>"


# --------------------------------------------------------------------------- #
# TaskEvent  (history log – schema only in Stage 1)
# --------------------------------------------------------------------------- #

class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        SAEnum(EventType, name="event_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    # JSON-serialisable dict of changed fields stored as plain text
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="events")

    def __repr__(self) -> str:
        return (
            f"<TaskEvent id={self.id!r} task_id={self.task_id!r}"
            f" event_type={self.event_type!r}>"
        )
