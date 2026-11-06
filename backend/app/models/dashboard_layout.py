import uuid
from datetime import datetime, timezone
from typing import Any, List
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.types import JSON

from app.db.session import Base

# Cross-database compatible JSON type: JSONB on Postgres, standard JSON on SQLite
JSONType = JSON().with_variant(JSONB, "postgresql")


class DashboardLayout(Base):
    """
    Per-user dashboard layout customization.
    Each user has at most one layout record (1:1 with User).
    When no record exists, the system serves the default layout from core/dashboard_registry.py.
    """

    __tablename__ = "dashboard_layouts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Serialized list of widget configurations:
    # [{'widget_id': str, 'is_visible': bool, 'order': int, 'size': str}, ...]
    widgets: Mapped[List[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship(
        "User",
        backref=backref("dashboard_layout", cascade="all, delete-orphan", uselist=False),
    )

    def __repr__(self) -> str:
        return f"<DashboardLayout(id={self.id}, user_id={self.user_id}, widgets_count={len(self.widgets) if self.widgets else 0})>"
