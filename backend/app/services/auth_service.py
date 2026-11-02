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
from app.models.security_token import SecurityToken, TokenType
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.security_token_repository import SecurityTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.email_service import get_email_provider
from app.services.rate_limit_service import RateLimitService

logger = logging.getLogger("dayflow.auth")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)
        self.security_token_repo = SecurityTokenRepository(db)
        self.email_provider = get_email_provider()
        self.rate_limit_service = RateLimitService(db)

    def _create_and_send_verification_token(self, user: User) -> str:
        """Create a new verification token and dispatch the verification email."""
        # Invalidate any previous unconsumed verification tokens for this user
        self.security_token_repo.revoke_existing_tokens_for_user(user.id, TokenType.EMAIL_VERIFICATION)

        raw_token = generate_secure_token(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

        token_record = SecurityToken(
            user_id=user.id,
            token_type=TokenType.EMAIL_VERIFICATION,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.security_token_repo.create(token_record)

        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
        self.email_provider.send_verification_email(
            to_email=user.email,
            display_name=user.display_name,
            verification_url=verification_url,
        )
        return raw_token

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        """Register a new user account and dispatch verification email."""
        normalized_email = payload.email.strip().lower()

        existing_user = self.user_repo.get_by_email(normalized_email)
        if existing_user:
            logger.warning("Registration attempt for existing email: %s", normalized_email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

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

        # Dispatch verification email
        try:
            self._create_and_send_verification_token(created_user)
        except Exception as exc:
            logger.error("Failed to send verification email: %s", exc)

        return UserResponse.model_validate(created_user)

    def verify_email(self, payload: VerifyEmailRequest) -> MessageResponse:
        """Verify an account email using a single-use token."""
        token_hash = hash_token(payload.token)
        token_record = self.security_token_repo.get_by_token_hash_for_update(token_hash)

        if not token_record or token_record.token_type != TokenType.EMAIL_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification link.",
            )

        if token_record.is_revoked or token_record.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This verification link has already been used or invalidated.",
            )

        if token_record.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This verification link has expired. Please request a new one.",
            )

        user = self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User associated with this token no longer exists.",
            )

        # Mark user as verified
        user.is_verified = True
        self.db.add(user)
        self.security_token_repo.mark_used(token_record)
        self.db.commit()

        logger.info("Successfully verified email for user id=%s", user.id)
        return MessageResponse(status="ok", message="Email address verified successfully.")

    def resend_verification(
        self,
        payload: ResendVerificationRequest,
        client_ip: Optional[str] = None,
    ) -> MessageResponse:
        """Resend verification email without leaking account existence, enforcing IP limit and email cooldown."""
        normalized_email = payload.email.strip().lower()

        # Enforce IP rate limit (HTTP 429 if exceeded)
        if client_ip:
            self.rate_limit_service.check_auth_email_rate_limit(
                client_ip=client_ip,
                email=normalized_email,
                action="resend_verification",
            )

        generic_message = (
            "If an unverified account exists for this email, a verification link has been sent."
        )

        user = self.user_repo.get_by_email(normalized_email)

        # Enforce email cooldown: only send if cooldown allows
        if user and not user.is_verified and user.is_active:
            can_send = self.rate_limit_service.check_and_apply_email_cooldown(
                email=normalized_email,
                action="resend_verification",
            )
            if can_send:
                try:
                    self._create_and_send_verification_token(user)
                except Exception as exc:
                    logger.error("Failed to resend verification email: %s", exc)

        return MessageResponse(status="ok", message=generic_message)

    def forgot_password(
        self,
        payload: ForgotPasswordRequest,
        client_ip: Optional[str] = None,
    ) -> MessageResponse:
        """Request a password reset link without leaking whether an account exists, enforcing IP limit and email cooldown."""
        normalized_email = payload.email.strip().lower()

        # Enforce IP rate limit (HTTP 429 if exceeded)
        if client_ip:
            self.rate_limit_service.check_auth_email_rate_limit(
                client_ip=client_ip,
                email=normalized_email,
                action="forgot_password",
            )

        generic_message = (
            "If an account exists with this email address, password reset instructions have been sent."
        )

        user = self.user_repo.get_by_email(normalized_email)

        # Enforce email cooldown: only send if cooldown allows
        if user and user.is_active:
            can_send = self.rate_limit_service.check_and_apply_email_cooldown(
                email=normalized_email,
                action="forgot_password",
            )
            if can_send:
                try:
                    # Invalidate existing active reset tokens for this user
                    self.security_token_repo.revoke_existing_tokens_for_user(user.id, TokenType.PASSWORD_RESET)

                    raw_token = generate_secure_token(32)
                    token_hash = hash_token(raw_token)
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

                    token_record = SecurityToken(
                        user_id=user.id,
                        token_type=TokenType.PASSWORD_RESET,
                        token_hash=token_hash,
                        expires_at=expires_at,
                    )
                    self.security_token_repo.create(token_record)

                    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
                    self.email_provider.send_password_reset_email(
                        to_email=user.email,
                        display_name=user.display_name,
                        reset_url=reset_url,
                    )
                except Exception as exc:
                    logger.error("Failed to send password reset email: %s", exc)

        return MessageResponse(status="ok", message=generic_message)

    def reset_password(self, payload: ResetPasswordRequest) -> MessageResponse:
        """Reset user password, invalidate reset token, and revoke all active refresh tokens."""
        token_hash = hash_token(payload.token)
        token_record = self.security_token_repo.get_by_token_hash_for_update(token_hash)

        if not token_record or token_record.token_type != TokenType.PASSWORD_RESET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link.",
            )

        if token_record.is_revoked or token_record.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This password reset link has already been used or invalidated.",
            )

        if token_record.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This password reset link has expired. Please request a new one.",
            )

        user = self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive or no longer exists.",
            )

        # Hash new password using Argon2id
        user.hashed_password = hash_password(payload.new_password)
        self.db.add(user)

        # Consume token
        self.security_token_repo.mark_used(token_record)

        # Revoke all active refresh sessions to force re-authentication everywhere
        revoked_sessions = self.token_repo.revoke_all_user_tokens(user.id)
        self.db.commit()

        logger.info(
            "Successfully reset password for user id=%s; revoked %d active refresh sessions",
            user.id,
            revoked_sessions,
        )
        return MessageResponse(
            status="ok",
            message="Your password has been reset successfully. Please sign in with your new password.",
        )

    def login(self, payload: UserLoginRequest) -> Tuple[TokenResponse, str]:
        """Authenticate user with email and password, returning access token & raw refresh token."""
        normalized_email = payload.email.strip().lower()
        user = self.user_repo.get_by_email(normalized_email)

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

        access_token = create_access_token(user_id=user.id)

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

        user = self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            logger.warning("Refresh attempt for invalid/inactive user id=%s", token_record.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
