import math
import uuid
import zoneinfo
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.calendar_event import CalendarEvent
from app.models.task import TaskPriority, TaskStatus
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.schemas.calendar_feed import (
    CalendarEventItem,
    CalendarFeedItem,
    CalendarFeedResponse,
    CalendarLinkedTaskSummary,
    CalendarTaskDeadlineItem,
    ScheduleTaskRequest,
)
from app.schemas.category import CategoryResponse
from app.schemas.project import ProjectResponse
from app.services.task_service import TaskService


class CalendarEventService:
    """Business logic for personal calendar events, unified feed, and task scheduling."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CalendarEventRepository(db)
        self.task_repo = TaskRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.proj_repo = ProjectRepository(db)

    def _to_response(self, event: CalendarEvent) -> CalendarEventResponse:
        return CalendarEventResponse.model_validate(event)

    def _validate_task_ownership(self, task_id: Optional[uuid.UUID], user_id: uuid.UUID) -> None:
        if task_id is not None:
            task = self.task_repo.get_by_id(task_id, user_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated task not found or does not belong to you.",
                )

    def create_event(self, payload: CalendarEventCreate, user_id: uuid.UUID) -> CalendarEventResponse:
        """Create a new calendar event for user after ownership and schema checks."""
        self._validate_task_ownership(payload.task_id, user_id)

        event = CalendarEvent(
            user_id=user_id,
            task_id=payload.task_id,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            color=payload.color,
            is_all_day=payload.is_all_day,
            timezone=payload.timezone,
            start_at=payload.start_at,
            end_at=payload.end_at,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

        created = self.repo.create(event, commit=True)
        return self._to_response(created)

    def get_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> CalendarEventResponse:
        """Retrieve a single event strictly scoped to user."""
        event = self.repo.get_by_id(event_id, user_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar event not found.",
            )
        return self._to_response(event)

    def update_event(
        self,
        event_id: uuid.UUID,
        payload: CalendarEventUpdate,
        user_id: uuid.UUID,
    ) -> CalendarEventResponse:
        """
        Update an existing event.
        Validates resulting full event state across partial updates.
        """
        event = self.repo.get_by_id_for_update(event_id, user_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar event not found.",
            )

        # Validate task ownership if changed
        if payload.task_id is not None:
            self._validate_task_ownership(payload.task_id, user_id)

        # Determine target state for representation validation
        target_is_all_day = payload.is_all_day if payload.is_all_day is not None else event.is_all_day
        target_start_at = payload.start_at if "start_at" in payload.model_fields_set else event.start_at
        target_end_at = payload.end_at if "end_at" in payload.model_fields_set else event.end_at
        target_start_date = payload.start_date if "start_date" in payload.model_fields_set else event.start_date
        target_end_date = payload.end_date if "end_date" in payload.model_fields_set else event.end_date

        if not target_is_all_day:
            if target_start_at is None or target_end_at is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Timed events require both 'start_at' and 'end_at'.",
                )
            if target_start_date is not None or target_end_date is not None:
                if payload.is_all_day is False and "start_date" not in payload.model_fields_set and "end_date" not in payload.model_fields_set:
                    target_start_date = None
                    target_end_date = None
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Timed events must not include all-day date fields.",
                    )
            if target_end_at <= target_start_at:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Timed event 'end_at' must be strictly after 'start_at'.",
                )
        else:
            if target_start_date is None or target_end_date is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="All-day events require both 'start_date' and 'end_date'.",
                )
            if target_start_at is not None or target_end_at is not None:
                if payload.is_all_day is True and "start_at" not in payload.model_fields_set and "end_at" not in payload.model_fields_set:
                    target_start_at = None
                    target_end_at = None
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="All-day events must not include timed timestamp fields.",
                    )
            if target_end_date <= target_start_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="All-day event 'end_date' must be strictly after 'start_date'.",
                )

        # Apply updates
        if payload.title is not None:
            event.title = payload.title
        if "description" in payload.model_fields_set:
            event.description = payload.description
        if "location" in payload.model_fields_set:
            event.location = payload.location
        if "color" in payload.model_fields_set:
            event.color = payload.color
        if payload.timezone is not None:
            event.timezone = payload.timezone
        if "task_id" in payload.model_fields_set:
            event.task_id = payload.task_id

        event.is_all_day = target_is_all_day
        event.start_at = target_start_at
        event.end_at = target_end_at
        event.start_date = target_start_date
        event.end_date = target_end_date

        updated = self.repo.update(event, commit=True)
        return self._to_response(updated)

    def delete_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete an event strictly scoped to user."""
        event = self.repo.get_by_id_for_update(event_id, user_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar event not found.",
            )
        self.repo.delete(event, commit=True)

    def list_events(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> CalendarEventListResponse:
        """List paginated calendar events."""
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        items, total = self.repo.list_events(user_id=user_id, offset=offset, limit=page_size)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return CalendarEventListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def schedule_task(self, payload: ScheduleTaskRequest, user_id: uuid.UUID) -> CalendarEventResponse:
        """Create a calendar time block associated with an existing task."""
        task = self.task_repo.get_by_id(payload.task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or does not belong to you.",
            )

        title = payload.title or task.title

        event = CalendarEvent(
            user_id=user_id,
            task_id=task.id,
            title=title,
            description=payload.description if payload.description is not None else task.description,
            color=payload.color,
            location=payload.location,
            is_all_day=False,
            timezone=payload.timezone,
            start_at=payload.start_at,
            end_at=payload.end_at,
            start_date=None,
            end_date=None,
        )

        created = self.repo.create(event, commit=True)
        return self._to_response(created)

    def get_unified_feed_from_strings(
        self,
        user_id: uuid.UUID,
        start_str: str,
        end_str: str,
        requested_tz_name: Optional[str] = None,
        include_tasks: bool = True,
        include_events: bool = True,
        project_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        task_status: Optional[TaskStatus] = None,
        task_priority: Optional[TaskPriority] = None,
        recurring_only: Optional[bool] = None,
    ) -> CalendarFeedResponse:
        """Parse raw query strings ensuring timezone offsets and delegate to get_unified_feed."""
        # Query string spaces may occur if + was decoded or raw string provided
        # e.g., '2026-11-10T00:00:00 00:00' -> '2026-11-10T00:00:00+00:00'
        clean_start = start_str.strip()
        clean_end = end_str.strip()

        # If a space precedes offset: e.g. '2026-11-10T00:00:00 00:00'
        if " " in clean_start and ("+" not in clean_start and "-" not in clean_start[10:]):
            clean_start = clean_start.replace(" ", "+")
        if " " in clean_end and ("+" not in clean_end and "-" not in clean_end[10:]):
            clean_end = clean_end.replace(" ", "+")

        try:
            start_dt = datetime.fromisoformat(clean_start)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid ISO-8601 format for 'start': '{start_str}'",
            )

        try:
            end_dt = datetime.fromisoformat(clean_end)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid ISO-8601 format for 'end': '{end_str}'",
            )

        if start_dt.tzinfo is None or end_dt.tzinfo is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date range 'start' and 'end' must include timezone offsets.",
            )

        return self.get_unified_feed(
            user_id=user_id,
            start=start_dt,
            end=end_dt,
            requested_tz_name=requested_tz_name,
            include_tasks=include_tasks,
            include_events=include_events,
            project_id=project_id,
            category_id=category_id,
            task_status=task_status,
            task_priority=task_priority,
            recurring_only=recurring_only,
        )

    def get_unified_feed(
        self,
        user_id: uuid.UUID,
        start: datetime,
        end: datetime,
        requested_tz_name: Optional[str] = None,
        include_tasks: bool = True,
        include_events: bool = True,
        project_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        task_status: Optional[TaskStatus] = None,
        task_priority: Optional[TaskPriority] = None,
        recurring_only: Optional[bool] = None,
    ) -> CalendarFeedResponse:
        """
        Unified feed combining calendar events and task deadlines.
        Enforces UTC conversions, half-open range [start, end), and max 93-day window.
        """
        # Validate timezone offsets
        if start.tzinfo is None or end.tzinfo is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date range 'start' and 'end' must include timezone offsets.",
            )

        if end <= start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'end' must be strictly after 'start'.",
            )

        # Enforce max 93-day window (approx 3 calendar months)
        if (end - start) > timedelta(days=93):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Calendar range exceeds maximum supported window of 93 days.",
            )

        # Validate IANA timezone if specified
        tz_str = requested_tz_name.strip() if requested_tz_name else "UTC"
        try:
            user_tz = zoneinfo.ZoneInfo(tz_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid IANA timezone identifier: '{tz_str}'",
            )

        # Convert boundaries to UTC
        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        # Local dates in requested timezone for all-day event boundary comparison
        local_start_date = start.astimezone(user_tz).date()
        local_end_date = end.astimezone(user_tz).date()

        # Validate optional filter IDs ownership
        if project_id is not None:
            proj = self.proj_repo.get_by_id(project_id, user_id)
            if not proj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project filter ID not found or does not belong to you.",
                )
        if category_id is not None:
            cat = self.cat_repo.get_by_id(category_id, user_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category filter ID not found or does not belong to you.",
                )

        feed_items: List[CalendarFeedItem] = []

        # 1. Fetch Calendar Events if included
        if include_events and recurring_only is not True:
            events = self.repo.get_events_for_range(
                user_id=user_id,
                range_start_utc=start_utc,
                range_end_utc=end_utc,
                local_start_date=local_start_date,
                local_end_date=local_end_date,
            )

            for ev in events:
                # If event is linked to a task and task filters are present, check linked task matching
                if ev.task_id is not None and ev.task:
                    if project_id and ev.task.project_id != project_id:
                        continue
                    if category_id and ev.task.category_id != category_id:
                        continue
                    if task_status and ev.task.status != task_status:
                        continue
                    if task_priority and ev.task.priority != task_priority:
                        continue
                elif project_id or category_id or task_status or task_priority:
                    # Standalone event without task link is omitted if specific task filters were requested
                    continue

                linked_summary = None
                if ev.task:
                    linked_summary = CalendarLinkedTaskSummary(
                        id=ev.task.id,
                        title=ev.task.title,
                        status=ev.task.status,
                        priority=ev.task.priority,
                        due_date=ev.task.due_date,
                    )

                feed_items.append(
                    CalendarEventItem(
                        id=ev.id,
                        type="event",
                        title=ev.title,
                        description=ev.description,
                        location=ev.location,
                        color=ev.color,
                        is_all_day=ev.is_all_day,
                        timezone=ev.timezone,
                        start_at=ev.start_at,
                        end_at=ev.end_at,
                        start_date=ev.start_date,
                        end_date=ev.end_date,
                        task_id=ev.task_id,
                        task=linked_summary,
                        created_at=ev.created_at,
                        updated_at=ev.updated_at,
                    )
                )

        # 2. Fetch Tasks with due_date if included
        if include_tasks:
            tasks = self.task_repo.get_tasks_for_calendar_range(
                user_id=user_id,
                range_start=start_utc,
                range_end=end_utc,
                project_id=project_id,
                category_id=category_id,
                status=task_status,
                priority=task_priority,
                recurring_only=recurring_only,
            )

            now_utc = datetime.now(timezone.utc)
            for t in tasks:
                if not t.due_date:
                    continue

                is_overdue = TaskService._is_task_overdue(t, now=now_utc)
                proj_resp = ProjectResponse.model_validate(t.project) if t.project else None
                cat_resp = CategoryResponse.model_validate(t.category) if t.category else None

                feed_items.append(
                    CalendarTaskDeadlineItem(
                        id=t.id,
                        type="task_deadline",
                        title=t.title,
                        description=t.description,
                        status=t.status,
                        priority=t.priority,
                        start_date=t.start_date,
                        due_date=t.due_date,
                        project_id=t.project_id,
                        project=proj_resp,
                        category_id=t.category_id,
                        category=cat_resp,
                        recurring_task_id=t.recurring_task_id,
                        occurrence_date=t.occurrence_date,
                        occurrence_index=t.occurrence_index,
                        is_overdue=is_overdue,
                        created_at=t.created_at,
                        updated_at=t.updated_at,
                    )
                )

        # Deterministic sorting:
        # Key = (start_datetime_utc, item_type_order, id_as_str)
        def sort_key(item: CalendarFeedItem):
            if item.type == "event":
                if item.is_all_day and item.start_date:
                    # Treat start_date as local midnight in user_tz converted to UTC
                    dt = datetime.combine(item.start_date, datetime.min.time(), tzinfo=user_tz).astimezone(timezone.utc)
                elif item.start_at:
                    dt = item.start_at if item.start_at.tzinfo else item.start_at.replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.min.replace(tzinfo=timezone.utc)
                return (dt, 0, str(item.id))
            else:
                due = item.due_date if item.due_date.tzinfo else item.due_date.replace(tzinfo=timezone.utc)
                return (due, 1, str(item.id))

        feed_items.sort(key=sort_key)

        return CalendarFeedResponse(
            items=feed_items,
            range_start=start_utc,
            range_end=end_utc,
            timezone=tz_str,
            total=len(feed_items),
        )
