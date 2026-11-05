import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.recurring_task import RecurrenceFrequency
from app.models.user import User
from app.schemas.recurring_task import (
    RecurringTaskCreateRequest,
    RecurringTaskListResponse,
    RecurringTaskResponse,
    RecurringTaskSkipRequest,
    RecurringTaskUpdateRequest,
    TriggerGenerationRequest,
)
from app.schemas.task import TaskListResponse
from app.services.recurring_task_service import RecurringTaskService

router = APIRouter(prefix="/recurring-tasks", tags=["Recurring Tasks"])


@router.post("", response_model=RecurringTaskResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_task(
    payload: RecurringTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Create a new recurring task series rule."""
    service = RecurringTaskService(db)
    return service.create_series(user_id=current_user.id, payload=payload)


@router.get("", response_model=RecurringTaskListResponse)
def list_recurring_tasks(
    frequency: Optional[RecurrenceFrequency] = Query(None, description="Filter by frequency"),
    is_active: Optional[bool] = Query(None, description="Filter active vs paused"),
    is_stopped: Optional[bool] = Query(None, description="Filter stopped status"),
    search: Optional[str] = Query(None, description="Search title or description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskListResponse:
    """List recurring task series owned by the current user."""
    service = RecurringTaskService(db)
    return service.list_series(
        user_id=current_user.id,
        frequency=frequency,
        is_active=is_active,
        is_stopped=is_stopped,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{id}", response_model=RecurringTaskResponse)
def get_recurring_task(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Retrieve recurring task series details."""
    service = RecurringTaskService(db)
    return service.get_series(series_id=id, user_id=current_user.id)


@router.patch("/{id}", response_model=RecurringTaskResponse)
def update_recurring_task(
    id: uuid.UUID,
    payload: RecurringTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Update recurring task series configuration."""
    service = RecurringTaskService(db)
    return service.update_series(series_id=id, user_id=current_user.id, payload=payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_task(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a recurring task series."""
    service = RecurringTaskService(db)
    service.delete_series(series_id=id, user_id=current_user.id)


@router.post("/{id}/pause", response_model=RecurringTaskResponse)
def pause_recurring_task(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Pause recurrence generation for a series."""
    service = RecurringTaskService(db)
    return service.pause_series(series_id=id, user_id=current_user.id)


@router.post("/{id}/resume", response_model=RecurringTaskResponse)
def resume_recurring_task(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Resume recurrence generation for a paused series."""
    service = RecurringTaskService(db)
    return service.resume_series(series_id=id, user_id=current_user.id)


@router.post("/{id}/stop", response_model=RecurringTaskResponse)
def stop_recurring_task(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Permanently stop recurrence generation for a series."""
    service = RecurringTaskService(db)
    return service.stop_series(series_id=id, user_id=current_user.id)


@router.get("/{id}/occurrences", response_model=TaskListResponse)
def list_recurring_task_occurrences(
    id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """List generated task occurrences for a recurring series."""
    service = RecurringTaskService(db)
    return service.list_occurrences(series_id=id, user_id=current_user.id, page=page, page_size=page_size)


@router.post("/{id}/skip", response_model=RecurringTaskResponse)
def skip_recurring_task_occurrence(
    id: uuid.UUID,
    payload: RecurringTaskSkipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTaskResponse:
    """Skip a specific scheduled occurrence date."""
    service = RecurringTaskService(db)
    return service.skip_occurrence(series_id=id, user_id=current_user.id, payload=payload)


MAX_GENERATION_FUTURE_DAYS = 30


@router.post("/trigger-generation", response_model=dict)
def trigger_generation(
    payload: Optional[TriggerGenerationRequest] = None,
    target_date: Optional[date] = Query(None, description="Generate up to target date (max 30 days into future)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger generation of due occurrences for the authenticated user."""
    today = datetime.now(timezone.utc).date()
    # Support target_date via query parameter or JSON request body
    effective_target = (payload.target_date if payload and payload.target_date else target_date) or today

    # Validate future-date limit
    max_allowed = today + timedelta(days=MAX_GENERATION_FUTURE_DAYS)
    if effective_target > max_allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Target date cannot exceed {MAX_GENERATION_FUTURE_DAYS} days into the future (max allowed: {max_allowed.isoformat()}).",
        )

    service = RecurringTaskService(db)
    created_count = service.generate_due_occurrences(user_id=current_user.id, target_date=effective_target)
    return {"status": "success", "created_occurrences": created_count}

