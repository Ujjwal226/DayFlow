import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.focus import (
    FocusAnalyticsOverview,
    FocusDailySummary,
    FocusPreferenceResponse,
    FocusPreferenceUpdate,
    FocusSessionResponse,
    FocusSessionStart,
    FocusWeeklyTrends,
)
from app.services.focus_service import FocusService

router = APIRouter(prefix="/focus", tags=["Focus & Pomodoro"])


@router.get("/active", response_model=Optional[FocusSessionResponse])
def get_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's current ACTIVE or PAUSED focus session, or null if none."""
    service = FocusService(db)
    return service.get_active_session(current_user.id)


@router.post("/start", response_model=FocusSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    data: FocusSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new focus or break session. Rejects if active session exists."""
    service = FocusService(db)
    return service.start_session(current_user.id, data)


@router.post("/sessions/{session_id}/pause", response_model=FocusSessionResponse)
def pause_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pause an active session."""
    service = FocusService(db)
    return service.pause_session(current_user.id, session_id)


@router.post("/sessions/{session_id}/resume", response_model=FocusSessionResponse)
def resume_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume a paused session."""
    service = FocusService(db)
    return service.resume_session(current_user.id, session_id)


@router.post("/sessions/{session_id}/complete", response_model=FocusSessionResponse)
def complete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete a session and record actual focus time."""
    service = FocusService(db)
    return service.complete_session(current_user.id, session_id)


@router.post("/sessions/{session_id}/abandon", response_model=FocusSessionResponse)
def abandon_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel or abandon a session without counting towards completed Pomodoros."""
    service = FocusService(db)
    return service.abandon_session(current_user.id, session_id)


@router.post("/sessions/{session_id}/skip", response_model=FocusSessionResponse)
def skip_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Skip the current session and transition safely to the next configured session in the cycle."""
    service = FocusService(db)
    return service.skip_session(current_user.id, session_id)


@router.get("/sessions/{session_id}", response_model=FocusSessionResponse)
def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific focus session with ownership validation."""
    service = FocusService(db)
    return service.get_session(current_user.id, session_id)


@router.get("/history", response_model=List[FocusSessionResponse])
def list_history(
    status_filter: Optional[str] = Query(None, alias="status"),
    session_type: Optional[str] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List historical focus and break sessions with filters."""
    service = FocusService(db)
    return service.list_history(
        user_id=current_user.id,
        status_filter=status_filter,
        session_type=session_type,
        task_id=task_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


@router.get("/preferences", response_model=FocusPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve user focus & timer preferences."""
    service = FocusService(db)
    return service.get_or_create_preferences(current_user.id)


@router.patch("/preferences", response_model=FocusPreferenceResponse)
def update_preferences(
    data: FocusPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user focus & timer preferences."""
    service = FocusService(db)
    return service.update_preferences(current_user.id, data)


@router.get("/analytics", response_model=FocusAnalyticsOverview)
def get_analytics(
    tz: str = Query("UTC", description="User local timezone"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete focus analytics overview including daily goals and task breakdowns."""
    service = FocusService(db)
    return service.get_analytics_overview(current_user.id, tz)
