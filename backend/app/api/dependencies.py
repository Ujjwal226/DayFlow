import ipaddress
import logging
import uuid
from typing import Optional
from urllib.parse import urlparse
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("dayflow.auth.dependencies")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency extracting the JWT access token and returning the active authenticated User."""
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        logger.warning("Access token validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_uuid)
    if not user:
        logger.warning("Token subject user id=%s not found", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Authenticated user id=%s is inactive", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


def validate_csrf_origin(
    request: Request,
    origin: Optional[str] = Header(None),
    referer: Optional[str] = Header(None),
) -> None:
    """Validate Origin/Referer against allowed origins for state-changing cookie operations."""
    # If safe read-only method, skip
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    client_origin = origin
    if not client_origin and referer:
        parsed = urlparse(referer)
        client_origin = f"{parsed.scheme}://{parsed.netloc}"

    # If in test/dev environment and no origin/referer header was sent (e.g. standard curl/direct test), allow
    if not client_origin:
        if settings.APP_ENV != "production":
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Origin header for state-changing request.",
        )

    allowed = settings.BACKEND_CORS_ORIGINS
    if isinstance(allowed, str):
        allowed = [allowed]

    if client_origin not in allowed:
        logger.warning("CSRF origin validation failed for origin: %s", client_origin)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-site request forgery protection: Origin not allowed.",
        )


def _is_ip_in_trusted_proxies(client_ip_str: str) -> bool:
    """Check if the direct peer IP belongs to configured trusted proxies."""
    if not settings.TRUSTED_PROXIES:
        return False

    trusted_list = settings.TRUSTED_PROXIES
    if isinstance(trusted_list, str):
        trusted_list = [trusted_list]

    for item in trusted_list:
        item = item.strip()
        if not item:
            continue
        if item.lower() == client_ip_str.lower():
            return True
        try:
            ip = ipaddress.ip_address(client_ip_str)
            if "/" in item:
                if ip in ipaddress.ip_network(item, strict=False):
                    return True
            else:
                if ip == ipaddress.ip_address(item):
                    return True
        except ValueError:
            continue
    return False


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address.

    Security Rule:
    Do not blindly trust arbitrary X-Forwarded-For or X-Real-IP headers.
    Forwarded headers are ONLY evaluated if the immediate connection (peer) originates
    from a configured trusted proxy (settings.TRUSTED_PROXIES).
    Otherwise, the direct peer address (request.client.host) is authoritative.
    """
    peer_ip = "127.0.0.1"
    if request.client and request.client.host:
        peer_ip = request.client.host.strip()

    # If the direct peer is NOT a trusted proxy, ignore all forwarded headers
    if not _is_ip_in_trusted_proxies(peer_ip):
        return peer_ip

    # Peer is a trusted proxy, inspect forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # The leftmost IP is the original client IP
        client_candidate = forwarded_for.split(",")[0].strip()
        if client_candidate:
            return client_candidate

    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    return peer_ip

