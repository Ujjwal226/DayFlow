import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base


class ActivityEntityType(str, enum.Enum):
    TASK = "TASK"
    SUBTASK = "SUBTASK"
    PROJECT = "PROJECT"
    RECURRING_TASK = "RECURRING_TASK"
    CATEGORY = "CATEGORY"
    TAG = "TAG"


class ActivityAction(str, enum.Enum):
    # Task actions
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    TASK_DELETED = "TASK_DELETED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_REOPENED = "TASK_REOPENED"
    TASK_ARCHIVED = "TASK_ARCHIVED"
    TASK_RESTORED = "TASK_RESTORED"
    TASK_DUPLICATED = "TASK_DUPLICATED"

    # Subtask actions
    SUBTASK_CREATED = "SUBTASK_CREATED"
    SUBTASK_UPDATED = "SUBTASK_UPDATED"
    SUBTASK_COMPLETED = "SUBTASK_COMPLETED"
    SUBTASK_DELETED = "SUBTASK_DELETED"

    # Project actions
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    PROJECT_RESTORED = "PROJECT_RESTORED"
    PROJECT_DELETED = "PROJECT_DELETED"

    # Recurring series actions
    RECURRING_SERIES_CREATED = "RECURRING_SERIES_CREATED"
    RECURRING_SERIES_UPDATED = "RECURRING_SERIES_UPDATED"
    RECURRING_SERIES_PAUSED = "RECURRING_SERIES_PAUSED"
    RECURRING_SERIES_RESUMED = "RECURRING_SERIES_RESUMED"
    RECURRING_SERIES_STOPPED = "RECURRING_SERIES_STOPPED"
    RECURRING_SERIES_DELETED = "RECURRING_SERIES_DELETED"
    RECURRING_OCCURRENCE_GENERATED = "RECURRING_OCCURRENCE_GENERATED"
    RECURRING_OCCURRENCE_SKIPPED = "RECURRING_OCCURRENCE_SKIPPED"

    # Categories & tags
    CATEGORY_CREATED = "CATEGORY_CREATED"
    CATEGORY_UPDATED = "CATEGORY_UPDATED"
    CATEGORY_DELETED = "CATEGORY_DELETED"
    TAG_CREATED = "TAG_CREATED"
    TAG_UPDATED = "TAG_UPDATED"
    TAG_DELETED = "TAG_DELETED"
    TAG_ASSIGNED = "TAG_ASSIGNED"
    TAG_REMOVED = "TAG_REMOVED"


# Cross-database compatible JSON type: JSONB on Postgres, standard JSON on SQLite
JSONType = JSON().with_variant(JSONB, "postgresql")


class ActivityLog(Base):
    """
    Immutable, append-only activity log / audit trail record.
    Tracks user operations across tasks, subtasks, projects, and recurrence rules.
    Foreign keys to entities use SET NULL so activity logs survive entity deletions.
    """

    __tablename__ = "activity_logs"

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

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    recurring_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recurring_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
    )

    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONType,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="activity_logs")
    actor = relationship("User", foreign_keys=[actor_id])
    task = relationship("Task", foreign_keys=[task_id])
    recurring_task = relationship("RecurringTask", foreign_keys=[recurring_task_id])

    __table_args__ = (
        Index("ix_activity_logs_user_created", "user_id", "created_at"),
        Index("ix_activity_logs_task_created", "task_id", "created_at"),
        Index("ix_activity_logs_recurring_created", "recurring_task_id", "created_at"),
        Index("ix_activity_logs_user_action", "user_id", "action"),
        Index("ix_activity_logs_user_entity", "user_id", "entity_type", "entity_id"),
    )

