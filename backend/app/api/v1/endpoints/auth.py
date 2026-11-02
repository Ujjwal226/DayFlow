from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, validate_csrf_origin
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    auth_service = AuthService(db)
    return auth_service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive access token",
)
def login(
    payload: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(db)
    token_response, refresh_token = auth_service.login(payload)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token",
    dependencies=[Depends(validate_csrf_origin)],
)
def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    dayflow_refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
) -> TokenResponse:
    auth_service = AuthService(db)
    token_response, new_refresh_token = auth_service.refresh_tokens(dayflow_refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return token_response


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke current refresh token session",
    dependencies=[Depends(validate_csrf_origin)],
)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    dayflow_refresh_token: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
) -> MessageResponse:
    auth_service = AuthService(db)
    auth_service.logout(dayflow_refresh_token)
    _clear_refresh_cookie(response)
    return MessageResponse(status="ok", message="Successfully logged out.")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout from all active sessions and revoke all refresh tokens",
)
def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)
    revoked_count = auth_service.logout_all(current_user.id)
    _clear_refresh_cookie(response)
    return MessageResponse(
        status="ok",
        message=f"Successfully revoked {revoked_count} active sessions.",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)

