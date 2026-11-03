import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TaskTag(Base):
    """Explicit association table for Task and Tag many-to-many relationship."""

    __tablename__ = "task_tags"

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_task_tags_tag_id_task_id", "tag_id", "task_id"),
    )


class Tag(Base):
    """Reusable tag owned strictly by an authenticated user."""

    __tablename__ = "tags"

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
        String(50),
        nullable=False,
    )
    name_normalized: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(7),
        nullable=True,
        default="#0D9488",  # Teal default
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
    user = relationship("User", backref="tags")
    tasks = relationship("Task", secondary="task_tags", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("user_id", "name_normalized", name="uq_tags_user_id_name_normalized"),
        Index("ix_tags_user_id_name_normalized", "user_id", "name_normalized"),
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, user_id={self.user_id}, name='{self.name}')>"
