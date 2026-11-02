import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_token_hash_for_update(self, token_hash: str) -> Optional[RefreshToken]:
        """Fetch token by its SHA-256 hash with pessimistic locking for concurrency protection."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def revoke_token(
        self,
        token: RefreshToken,
        replaced_by_id: Optional[uuid.UUID] = None,
    ) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        token.last_used_at = datetime.now(timezone.utc)
        if replaced_by_id:
            token.replaced_by_id = replaced_by_id
        self.db.add(token)
        self.db.commit()

    def revoke_family(self, family_id: uuid.UUID) -> int:
        """Revoke all active tokens belonging to a family (reuse/theft detection)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now, last_used_at=now)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for a user across all sessions/devices."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now, last_used_at=now)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def get_active_by_user(self, user_id: uuid.UUID) -> List[RefreshToken]:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        return list(self.db.execute(stmt).scalars().all())

