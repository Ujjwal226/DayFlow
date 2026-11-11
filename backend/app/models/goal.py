import enum
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class GoalCategory(str, enum.Enum):
    PERSONAL = "PERSONAL"
    CAREER = "CAREER"
    LEARNING = "LEARNING"
    HEALTH = "HEALTH"
    FINANCE = "FINANCE"
    PROJECTS = "PROJECTS"
    OTHER = "OTHER"


class GoalType(str, enum.Enum):
    OUTCOME = "OUTCOME"
    NUMERIC = "NUMERIC"
    MILESTONE = "MILESTONE"


class GoalStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class GoalPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ProgressCalculationMethod(str, enum.Enum):
    MANUAL = "MANUAL"
    MILESTONE = "MILESTONE"
    NUMERIC = "NUMERIC"


class PlanningPeriodType(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class GoalTaskLink(Base):
    """Many-to-many relationship table linking tasks to goals."""

    __tablename__ = "goal_task_links"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    goal = relationship("Goal", back_populates="task_links")
    task = relationship("Task", backref="goal_links")

    __table_args__ = (
        UniqueConstraint("goal_id", "task_id", name="uq_goal_task_link"),
    )


class Goal(Base):
    """Goal owned strictly by an authenticated user."""

    __tablename__ = "goals"

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
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category: Mapped[str] = mapped_column(String(32), default=GoalCategory.PERSONAL.value, nullable=False, index=True)
    goal_type: Mapped[str] = mapped_column(String(32), default=GoalType.OUTCOME.value, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default=GoalStatus.NOT_STARTED.value, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), default=GoalPriority.MEDIUM.value, nullable=False, index=True)

    progress_method: Mapped[str] = mapped_column(
        String(32), default=ProgressCalculationMethod.MANUAL.value, nullable=False
    )
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Numeric target fields
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

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

    user = relationship("User", backref="goals")
    project = relationship("Project", backref="goals")
    milestones = relationship(
        "GoalMilestone",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="GoalMilestone.order_index",
    )
    task_links = relationship("GoalTaskLink", back_populates="goal", cascade="all, delete-orphan")
    planning_objectives = relationship("PlanningObjective", back_populates="goal", cascade="all, delete-orphan")
    activities = relationship(
        "GoalActivity",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="desc(GoalActivity.created_at)",
    )

    __table_args__ = (
        Index("ix_goals_user_status", "user_id", "status"),
        Index("ix_goals_user_category", "user_id", "category"),
        Index("ix_goals_user_target_date", "user_id", "target_date"),
        Index("ix_goals_user_archived", "user_id", "is_archived"),
    )


class GoalMilestone(Base):
    """Milestone representing an incremental checkpoint for a goal."""

    __tablename__ = "goal_milestones"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    goal = relationship("Goal", back_populates="milestones")
    user = relationship("User")

    __table_args__ = (
        Index("ix_goal_milestones_user_goal", "user_id", "goal_id"),
    )


class PlanningObjective(Base):
    """Daily, weekly, or monthly objective linked optionally to goals and tasks."""

    __tablename__ = "planning_objectives"

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
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    period_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # DAILY, WEEKLY, MONTHLY
    period_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # Reference date for day/week/month start

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default=GoalPriority.MEDIUM.value, nullable=False)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    user = relationship("User")
    goal = relationship("Goal", back_populates="planning_objectives")
    task = relationship("Task")

    __table_args__ = (
        Index("ix_planning_objectives_user_period", "user_id", "period_type", "period_date"),
    )


class GoalActivity(Base):
    """Activity and audit event log for goal changes."""

    __tablename__ = "goal_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, UPDATED, STATUS_CHANGED, PROGRESS_UPDATED, MILESTONE_ADDED, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    goal = relationship("Goal", back_populates="activities")
    user = relationship("User")

    __table_args__ = (
        Index("ix_goal_activities_goal_created", "goal_id", "created_at"),
        Index("ix_goal_activities_user_created", "user_id", "created_at"),
    )
