from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reminder import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@router.get("", response_model=NotificationPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve user notification preferences (or defaults)."""
    service = NotificationService(db)
    return service.get_or_create_preferences(current_user.id)


@router.patch("", response_model=NotificationPreferenceResponse)
def update_preferences(
    data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user notification preferences."""
    service = NotificationService(db)
    return service.update_preferences(current_user.id, data)
