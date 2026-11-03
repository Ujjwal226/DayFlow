import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Category(Base):
    """Custom category owned strictly by an authenticated user."""

    __tablename__ = "categories"

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
        String(100),
        nullable=False,
    )
    name_normalized: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#10B981",  # Emerald default
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
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
    user = relationship("User", backref="categories")
    tasks = relationship("Task", back_populates="category")

    __table_args__ = (
        UniqueConstraint("user_id", "name_normalized", name="uq_categories_user_id_name_normalized"),
        Index("ix_categories_user_id_name_normalized", "user_id", "name_normalized"),
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

