import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

logger = logging.getLogger("dayflow.auth")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        """Register a new user account."""
        normalized_email = payload.email.strip().lower()

        # Check existing user
        existing_user = self.user_repo.get_by_email(normalized_email)
        if existing_user:
            logger.warning("Registration attempt for existing email: %s", normalized_email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        # Hash password using Argon2id
        hashed_pwd = hash_password(payload.password)

        user = User(
            email=normalized_email,
            display_name=payload.display_name.strip(),
            hashed_password=hashed_pwd,
            is_active=True,
            is_verified=False,
        )
        created_user = self.user_repo.create(user)
        logger.info("Successfully registered user id=%s email=%s", created_user.id, created_user.email)
        return UserResponse.model_validate(created_user)

    def login(self, payload: UserLoginRequest) -> Tuple[TokenResponse, str]:
        """Authenticate user with email and password, returning access token & raw refresh token."""
        normalized_email = payload.email.strip().lower()
        user = self.user_repo.get_by_email(normalized_email)

        # Return generic invalid credentials response
        if not user or not verify_password(payload.password, user.hashed_password):
            logger.warning("Failed login attempt for email: %s", normalized_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning("Login attempt for inactive user id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )

        # Generate JWT access token
        access_token = create_access_token(user_id=user.id)

        # Create refresh token session in a new family
        raw_refresh_token = generate_secure_token()
        token_hash = hash_token(raw_refresh_token)
        family_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self.token_repo.create(refresh_token_record)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, raw_refresh_token

    def refresh_tokens(self, raw_token: Optional[str]) -> Tuple[TokenResponse, str]:
        """Rotate refresh token atomically and detect reuse."""
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_hash = hash_token(raw_token)
        token_record = self.token_repo.get_by_token_hash_for_update(token_hash)

        if not token_record:
            logger.warning("Refresh attempt with unknown token hash")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Token Reuse Detection: If token is already revoked, revoke its whole family!
        if token_record.is_revoked:
            logger.error(
                "TOKEN REUSE DETECTED! Token id=%s family_id=%s was already revoked. Revoking all tokens in family.",
                token_record.id,
                token_record.family_id,
            )
            self.token_repo.revoke_family(token_record.family_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token session. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_record.is_expired:
            logger.warning("Refresh attempt with expired token id=%s", token_record.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check user status
        user = self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            logger.warning("Refresh attempt for invalid/inactive user id=%s", token_record.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Rotate: issue new access token & new refresh token under the same family
        new_access_token = create_access_token(user_id=user.id)
        new_raw_refresh = generate_secure_token()
        new_token_hash = hash_token(new_raw_refresh)
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,
            expires_at=new_expires_at,
        )
        created_new_record = self.token_repo.create(new_refresh_record)

        # Revoke old refresh token, linking to replacement
        self.token_repo.revoke_token(token_record, replaced_by_id=created_new_record.id)

        token_response = TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, new_raw_refresh

    def logout(self, raw_token: Optional[str]) -> None:
        """Revoke current refresh token session safely if present."""
        if not raw_token:
            return

        token_hash = hash_token(raw_token)
        token_record = self.token_repo.get_by_token_hash(token_hash)
        if token_record and not token_record.is_revoked:
            self.token_repo.revoke_token(token_record)
            logger.info("Successfully revoked refresh token id=%s", token_record.id)

    def logout_all(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for the given user."""
        count = self.token_repo.revoke_all_user_tokens(user_id)
        logger.info("Revoked %d active refresh tokens for user id=%s", count, user_id)
        return count

