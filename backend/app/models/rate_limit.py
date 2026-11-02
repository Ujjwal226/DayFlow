import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RateLimitScope(str, enum.Enum):
    CLIENT_IP = "client_ip"
    EMAIL = "email"


class RateLimitRecord(Base):
    """PostgreSQL-backed shared rate-limiting record for IP throttles and email cooldowns."""

    __tablename__ = "rate_limit_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # Action being throttled, e.g. "auth_email"
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # Scope: CLIENT_IP or EMAIL
    scope: Mapped[RateLimitScope] = mapped_column(
        Enum(RateLimitScope, name="rate_limit_scope"),
        nullable=False,
    )
    # Cryptographic SHA-256 hash of the identifier (IP or normalized email) with salt
    identifier_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    # Request count accumulated within the window
    request_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    # Window start time (UTC)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Expiration time for this record/window (UTC)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_rate_limit_action_scope_hash",
            "action",
            "scope",
            "identifier_hash",
            unique=True,
        ),
        Index("ix_rate_limit_records_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<RateLimitRecord(action='{self.action}', scope='{self.scope}', "
            f"count={self.request_count}, expires_at='{self.expires_at}')>"
        )

