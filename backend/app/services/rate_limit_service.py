import logging
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rate_limit import RateLimitScope
from app.repositories.rate_limit_repository import RateLimitRepository

logger = logging.getLogger("dayflow.rate_limit.service")


class RateLimitService:
    """Service to orchestrate rate limiting for authentication and sensitive flows."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RateLimitRepository(db)

    def check_auth_email_rate_limit(
        self,
        client_ip: str,
        email: str,
        action: str = "auth_email",
        now: Optional[datetime] = None,
    ) -> None:
        """
        Evaluate rate limit for authentication email requests:
        1. IP rate limit: max N requests per window (default: 3 requests per 15 minutes).
           If exceeded, raises HTTP 429 Too Many Requests with Retry-After header.
        2. Email cooldown: max 1 request per cooldown period (default: 2 minutes) per normalized email.
           If cooldown is active, silently skips email delivery while returning generic response,
           OR if IP limit applies, throttles without leaking email state.

        Note: To preserve generic response behavior and avoid account enumeration, email cooldown
        is enforced silently in business logic (preventing duplicate outbound emails within cooldown),
        while IP limit is enforced with standard HTTP 429 to protect infrastructure.
        """
        # Periodic light cleanup of expired records
        try:
            self.repo.cleanup_expired(now=now)
        except Exception as e:
            logger.warning("Failed to clean up expired rate limits: %s", e)

        # 1. Evaluate IP Limit
        normalized_ip = client_ip.strip() if client_ip else "unknown"
        ip_allowed, count, retry_after = self.repo.check_and_increment(
            action=action,
            scope=RateLimitScope.CLIENT_IP,
            raw_identifier=normalized_ip,
            max_requests=settings.AUTH_EMAIL_RATE_LIMIT_IP_MAX_REQUESTS,
            window_minutes=settings.AUTH_EMAIL_RATE_LIMIT_IP_WINDOW_MINUTES,
            now=now,
        )

        if not ip_allowed:
            logger.warning(
                "IP rate limit exceeded for action '%s' from IP '%s'. Count=%d, Retry-After=%ss",
                action,
                normalized_ip,
                count,
                retry_after,
            )
            # Commit the rate limit count increment so subsequent requests are still blocked
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a few minutes before trying again.",
                headers={"Retry-After": str(retry_after or 60)},
            )

        # Commit the IP rate limit check
        self.db.commit()

    def check_and_apply_email_cooldown(
        self,
        email: str,
        action: str = "auth_email",
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Check if normalized email is in active cooldown.
        If allowed: increments/records the cooldown window and returns True (proceed to send email).
        If cooling down: returns False (skip sending email, but keep caller generic response).
        """
        normalized_email = email.strip().lower()
        allowed, count, retry_after = self.repo.check_and_increment(
            action=action,
            scope=RateLimitScope.EMAIL,
            raw_identifier=normalized_email,
            max_requests=1,
            window_minutes=settings.AUTH_EMAIL_COOLDOWN_PER_EMAIL_MINUTES,
            now=now,
        )

        if not allowed:
            logger.info(
                "Email cooldown active for normalized email (hashed). Suppressing email send. Retry-After=%ss",
                retry_after,
            )
            self.db.commit()
            return False

        self.db.commit()
        return True

