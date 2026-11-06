from datetime import datetime
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.schemas.calendar_feed import (
    CalendarFeedResponse,
    ScheduleTaskRequest,
)
from app.services.calendar_event_service import CalendarEventService

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ---------------------------------------------------------
# Unified Calendar Feed
# ---------------------------------------------------------

@router.get(
    "/feed",
    response_model=CalendarFeedResponse,
    summary="Get unified calendar feed",
)
def get_unified_feed(
    start: str = Query(..., description="Start of range (ISO-8601 with tz offset)"),
    end: str = Query(..., description="End of range (ISO-8601 with tz offset)"),
    timezone: Optional[str] = Query("UTC", description="IANA timezone identifier"),
    include_tasks: bool = Query(True, description="Whether to include task deadlines"),
    include_events: bool = Query(True, description="Whether to include calendar events"),
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project UUID"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category UUID"),
    status: Optional[TaskStatus] = Query(None, description="Filter tasks by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter tasks by priority"),
    recurring_only: Optional[bool] = Query(None, description="Filter to recurring task occurrences only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarFeedResponse:
    """Retrieve an aggregated, chronological feed of calendar events and task deadlines within [start, end)."""
    service = CalendarEventService(db)
    return service.get_unified_feed_from_strings(
        user_id=current_user.id,
        start_str=start,
        end_str=end,
        requested_tz_name=timezone,
        include_tasks=include_tasks,
        include_events=include_events,
        project_id=project_id,
        category_id=category_id,
        task_status=status,
        task_priority=priority,
        recurring_only=recurring_only,
    )


# ---------------------------------------------------------
# Task Scheduling
# ---------------------------------------------------------

@router.post(
    "/events/schedule-task",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a time block for an existing task",
)
def schedule_task(
    payload: ScheduleTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    """Create a calendar time block linked to an existing task."""
    service = CalendarEventService(db)
    return service.schedule_task(payload, current_user.id)


# ---------------------------------------------------------
# Calendar Event CRUD
# ---------------------------------------------------------

@router.post(
    "/events",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a calendar event",
)
def create_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    """Create a new timed or all-day calendar event owned by the authenticated user."""
    service = CalendarEventService(db)
    return service.create_event(payload, current_user.id)


@router.get(
    "/events",
    response_model=CalendarEventListResponse,
    summary="List calendar events",
)
def list_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEventListResponse:
    """List paginated calendar events belonging to the authenticated user."""
    service = CalendarEventService(db)
    return service.list_events(current_user.id, page=page, page_size=page_size)


@router.get(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
    summary="Get calendar event details",
)
def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    """Get details of a specific calendar event."""
    service = CalendarEventService(db)
    return service.get_event(event_id, current_user.id)


@router.put(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
    summary="Update a calendar event",
)
def update_event(
    event_id: uuid.UUID,
    payload: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    """Update fields of an existing calendar event."""
    service = CalendarEventService(db)
    return service.update_event(event_id, payload, current_user.id)


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a calendar event",
)
def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a calendar event."""
    service = CalendarEventService(db)
    service.delete_event(event_id, current_user.id)
