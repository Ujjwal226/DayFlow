import enum
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ProjectStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class ProjectPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Project(Base):
    """Project owned strictly by an authenticated user."""

    __tablename__ = "projects"

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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.PLANNED,
        nullable=False,
        index=True,
    )
    priority: Mapped[ProjectPriority] = mapped_column(
        Enum(ProjectPriority, name="project_priority"),
        default=ProjectPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    color: Mapped[Optional[str]] = mapped_column(
        String(7),
        nullable=True,
        default="#3B82F6",  # Default Blue
    )

    is_archived: Mapped[bool] = mapped_column(
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
    user = relationship("User", backref="projects")
    tasks = relationship("Task", back_populates="project")

    __table_args__ = (
        Index("ix_projects_user_id_status", "user_id", "status"),
        Index("ix_projects_user_id_priority", "user_id", "priority"),
        Index("ix_projects_user_id_is_archived", "user_id", "is_archived"),
        Index("ix_projects_user_id_due_date", "user_id", "due_date"),
        Index("ix_projects_user_id_created_at", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, user_id={self.user_id}, name='{self.name[:30]}', status='{self.status}')>"

