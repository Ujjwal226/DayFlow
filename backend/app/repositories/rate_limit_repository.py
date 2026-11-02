import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rate_limit import RateLimitRecord, RateLimitScope

logger = logging.getLogger("dayflow.rate_limit.repository")


class RateLimitRepository:
    """PostgreSQL repository for querying, incrementing, and cleaning rate limits with row-level locks."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def hash_identifier(identifier: str, salt: Optional[str] = None) -> str:
        """Compute SHA-256 HMAC/hash of normalized identifier with salt to avoid storing raw IPs or emails."""
        effective_salt = salt if salt is not None else settings.RATE_LIMIT_SALT
        data = f"{effective_salt}:{identifier}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get_for_update(
        self,
        action: str,
        scope: RateLimitScope,
        identifier_hash: str,
    ) -> Optional[RateLimitRecord]:
        """Fetch rate limit record locking the row for update."""
        stmt = (
            select(RateLimitRecord)
            .where(
                RateLimitRecord.action == action,
                RateLimitRecord.scope == scope,
                RateLimitRecord.identifier_hash == identifier_hash,
            )
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def check_and_increment(
        self,
        action: str,
        scope: RateLimitScope,
        raw_identifier: str,
        max_requests: int,
        window_minutes: int,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Atomically evaluate and increment rate limit for a given action and scope.

        Returns:
            Tuple[bool, int, Optional[int]]:
                - is_allowed: True if request was permitted and counted; False if rate limit exceeded.
                - current_count: request count accumulated in the current window.
                - retry_after_seconds: seconds remaining until the window resets, if throttled.
        """
        current_time = now or datetime.now(timezone.utc)
        ident_hash = self.hash_identifier(raw_identifier)

        record = self.get_for_update(action, scope, ident_hash)

        if record is None:
            # First request in a new window. Use ON CONFLICT DO NOTHING to handle race conditions
            expires_at = current_time + timedelta(minutes=window_minutes)
            new_id = uuid.uuid4()
            insert_stmt = (
                pg_insert(RateLimitRecord)
                .values(
                    id=new_id,
                    action=action,
                    scope=scope,
                    identifier_hash=ident_hash,
                    request_count=1,
                    window_start=current_time,
                    expires_at=expires_at,
                )
                .on_conflict_do_nothing(
                    index_elements=["action", "scope", "identifier_hash"]
                )
            )
            result = self.db.execute(insert_stmt)
            if result.rowcount > 0:
                self.db.flush()
                return True, 1, None

            # Another concurrent thread inserted the record before us.
            # get_for_update blocks until that thread commits (or rolls back).
            record = self.get_for_update(action, scope, ident_hash)
            if record is None:
                # If thread 1 rolled back, recursively try again
                return self.check_and_increment(
                    action, scope, raw_identifier, max_requests, window_minutes, now=current_time
                )

            # Note: when thread 1 inserted and committed, record is now locked by our transaction.
            # Its request_count reflects thread 1's request. We must now evaluate thread 2's request:
            # Proceed directly to check if window expired, limit reached, or increment counter below!

        # Check if current window has expired
        record_expires_at = record.expires_at
        if record_expires_at.tzinfo is None:
            record_expires_at = record_expires_at.replace(tzinfo=timezone.utc)

        if current_time >= record_expires_at:
            # Window expired; reset window and counter
            record.request_count = 1
            record.window_start = current_time
            record.expires_at = current_time + timedelta(minutes=window_minutes)
            self.db.add(record)
            self.db.flush()
            return True, 1, None

        # Window is active: check limit
        if record.request_count >= max_requests:
            remaining_seconds = max(1, int((record_expires_at - current_time).total_seconds()))
            return False, record.request_count, remaining_seconds

        # Within limit: increment counter
        record.request_count += 1
        self.db.add(record)
        self.db.flush()
        return True, record.request_count, None

    def cleanup_expired(self, now: Optional[datetime] = None) -> int:
        """Purge all expired rate limit records to prevent table bloating."""
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        stmt = delete(RateLimitRecord).where(RateLimitRecord.expires_at < current_time)
        result = self.db.execute(stmt)
        deleted_count = result.rowcount or 0
        if deleted_count > 0:
            self.db.flush()
            logger.debug("Cleaned up %d expired rate limit records", deleted_count)
        return deleted_count
