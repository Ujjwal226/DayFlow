import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.security_token import SecurityToken, TokenType


class SecurityTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_token_hash_for_update(self, token_hash: str) -> Optional[SecurityToken]:
        """Fetch token by its SHA-256 hash with pessimistic locking for concurrency safety."""
        stmt = select(SecurityToken).where(SecurityToken.token_hash == token_hash).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_token_hash(self, token_hash: str) -> Optional[SecurityToken]:
        stmt = select(SecurityToken).where(SecurityToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, token: SecurityToken) -> SecurityToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def mark_used(self, token: SecurityToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.add(token)
        self.db.commit()

    def revoke_existing_tokens_for_user(self, user_id: uuid.UUID, token_type: TokenType) -> int:
        """Revoke all unused, active security tokens of a specific type for a user."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(SecurityToken)
            .where(
                SecurityToken.user_id == user_id,
                SecurityToken.token_type == token_type,
                SecurityToken.used_at.is_(None),
                SecurityToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

