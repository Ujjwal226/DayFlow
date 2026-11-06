from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardLayoutResponse,
    DashboardLayoutUpdateRequest,
)
from app.services.dashboard_layout_service import DashboardLayoutService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/layout",
    response_model=DashboardLayoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user dashboard layout configuration",
)
def get_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardLayoutResponse:
    """
    Retrieve the current dashboard layout configuration for the authenticated user.
    If the user has not customized their layout, returns the system default layout.
    """
    service = DashboardLayoutService(db)
    return service.get_layout(current_user.id)


@router.put(
    "/layout",
    response_model=DashboardLayoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user dashboard layout configuration",
)
def update_dashboard_layout(
    request: DashboardLayoutUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardLayoutResponse:
    """
    Update the dashboard layout configuration for the authenticated user.
    Uses full-replacement semantics to persist widget ordering, visibility, and sizing.
    """
    service = DashboardLayoutService(db)
    return service.update_layout(current_user.id, request)


@router.post(
    "/layout/reset",
    response_model=DashboardLayoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset user dashboard layout configuration to default",
)
def reset_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardLayoutResponse:
    """
    Reset the dashboard layout configuration for the authenticated user back to default.
    Removes customized configuration record from the database.
    """
    service = DashboardLayoutService(db)
    return service.reset_layout(current_user.id)

