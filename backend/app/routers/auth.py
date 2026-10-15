"""
DayFlow backend – authentication router (Stage 5).

Endpoints
---------
POST /auth/register
POST /auth/login
GET  /auth/me
POST /auth/logout
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: schemas.UserRegister,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address is required",
        )
    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters",
        )

    existing = crud.get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    hashed_pw = hash_password(payload.password)
    user = crud.create_user(db, payload, hashed_password=hashed_pw)

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    summary="Login with email and password",
)
def login(
    payload: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    user = crud.get_user_by_email(db, email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current authenticated user profile",
)
def get_me(current_user: models.User = Depends(get_current_user)):
    return schemas.UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=schemas.MessageResponse,
    summary="Logout user session",
)
def logout(current_user: models.User = Depends(get_current_user)):
    return schemas.MessageResponse(message="Successfully logged out")
