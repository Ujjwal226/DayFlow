import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func, text as sql_text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FocusSession(Base):
    """Pomodoro and focus session recording planned duration, actual elapsed time, and status."""

    __tablename__ = "focus_sessions"

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
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # session_type: FOCUS, SHORT_BREAK, LONG_BREAK
    session_type: Mapped[str] = mapped_column(String(32), default="FOCUS", nullable=False)
    # status: ACTIVE, PAUSED, COMPLETED, ABANDONED
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)

    planned_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accumulated_pause_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    user = relationship("User", backref="focus_sessions")
    task = relationship("Task", backref="focus_sessions")
    project = relationship("Project", backref="focus_sessions")

    __table_args__ = (
        Index("ix_focus_sessions_user_status", "user_id", "status"),
        Index("ix_focus_sessions_user_started", "user_id", "started_at"),
        Index(
            "uq_focus_sessions_user_active_or_paused",
            "user_id",
            unique=True,
            postgresql_where=sql_text("status IN ('ACTIVE', 'PAUSED')"),
            sqlite_where=sql_text("status IN ('ACTIVE', 'PAUSED')"),
        ),
    )


class FocusPreference(Base):
    """User preferences and configuration for Focus & Pomodoro timer."""

    __tablename__ = "focus_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    focus_duration_minutes: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    short_break_duration_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    long_break_duration_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    long_break_interval: Mapped[int] = mapped_column(Integer, default=4, nullable=False)

    auto_start_breaks: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_start_focus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    browser_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, default=120, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", backref="focus_preference", uselist=False)
