import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate,
    ReminderResponse,
    ReminderSnooze,
    ReminderUpdate,
)
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new personal reminder, optionally associated with a task."""
    service = ReminderService(db)
    return service.create_reminder(current_user.id, data)


@router.get("", response_model=List[ReminderResponse])
def list_reminders(
    status_filter: Optional[str] = Query(None, alias="status"),
    task_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's reminders with optional status and task filtering."""
    service = ReminderService(db)
    return service.list_reminders(
        user_id=current_user.id,
        status_filter=status_filter,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a reminder by ID."""
    service = ReminderService(db)
    return service.get_reminder(reminder_id, current_user.id)


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update reminder attributes."""
    service = ReminderService(db)
    return service.update_reminder(reminder_id, current_user.id, data)


@router.post("/{reminder_id}/snooze", response_model=ReminderResponse)
def snooze_reminder(
    reminder_id: uuid.UUID,
    data: ReminderSnooze,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Snooze a reminder by N minutes."""
    service = ReminderService(db)
    return service.snooze_reminder(reminder_id, current_user.id, data)


@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
def complete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a reminder as completed."""
    service = ReminderService(db)
    return service.complete_reminder(reminder_id, current_user.id)


@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
def dismiss_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismiss a reminder without marking complete."""
    service = ReminderService(db)
    return service.dismiss_reminder(reminder_id, current_user.id)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a reminder permanently."""
    service = ReminderService(db)
    service.delete_reminder(reminder_id, current_user.id)
