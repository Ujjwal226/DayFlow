"""
DayFlow backend – CRUD helpers.

All database operations live here so routers stay thin.
Business logic (e.g. setting completed_at, logging task events) lives here.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models, schemas


# --------------------------------------------------------------------------- #
# Event logging helper
# --------------------------------------------------------------------------- #

def _log_event(
    db: Session,
    task_id: int,
    event_type: models.EventType | str,
    details: Optional[Dict[str, Any]] = None,
) -> models.TaskEvent:
    """Create and persist a task event."""
    et_val = event_type.value if hasattr(event_type, "value") else str(event_type)
    details_str = json.dumps(details, default=str) if details is not None else None
    event = models.TaskEvent(
        task_id=task_id,
        event_type=et_val,
        event_timestamp=datetime.now(timezone.utc),
        details=details_str,
    )
    db.add(event)
    return event


# --------------------------------------------------------------------------- #
# Task CRUD
# --------------------------------------------------------------------------- #

def get_task(db: Session, task_id: int, include_deleted: bool = False) -> Optional[models.Task]:
    """Return a task by ID. If include_deleted is False, excludes soft-deleted tasks."""
    stmt = select(models.Task).where(models.Task.id == task_id)
    if not include_deleted:
        stmt = stmt.where(models.Task.deleted_at.is_(None))
    return db.scalars(stmt).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
) -> tuple[List[models.Task], int]:
    """
    Return a paginated list of non-deleted tasks and the total count.

    Optional filters: status, category, priority.
    """
    stmt = select(models.Task).where(models.Task.deleted_at.is_(None))

    if status:
        stmt = stmt.where(models.Task.status == status)
    if category:
        stmt = stmt.where(models.Task.category == category)
    if priority:
        stmt = stmt.where(models.Task.priority == priority)

    # Total count before pagination
    count_stmt = stmt.with_only_columns(
        models.Task.id
    ).order_by(None)
    total = len(db.scalars(count_stmt).all())

    stmt = stmt.order_by(models.Task.scheduled_date, models.Task.id).offset(skip).limit(limit)
    tasks = list(db.scalars(stmt).all())
    return tasks, total


def create_task(db: Session, payload: schemas.TaskCreate) -> models.Task:
    """Create a new task, preserving original_scheduled_date and logging created event."""
    data = payload.model_dump()
    task = models.Task(
        **data,
        original_scheduled_date=data["scheduled_date"],
        status=models.TaskStatus.pending.value,
    )
    db.add(task)
    db.flush()  # assign task.id before logging event

    _log_event(
        db,
        task_id=task.id,
        event_type=models.EventType.created,
        details={
            "title": task.title,
            "scheduled_date": str(task.scheduled_date),
            "start_time": str(task.start_time) if task.start_time else None,
            "end_time": str(task.end_time) if task.end_time else None,
            "priority": task.priority,
            "category": task.category,
        },
    )

    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task: models.Task,
    payload: schemas.TaskUpdate,
) -> models.Task:
    """
    Apply non-None fields from payload to the task.

    Detects if scheduled_date/time changed to log 'rescheduled' event,
    or otherwise logs 'updated' event with change details.
    """
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        return task

    old_scheduled_date = task.scheduled_date
    old_start_time = task.start_time
    old_end_time = task.end_time

    changes: Dict[str, Any] = {}
    is_reschedule = False

    if "scheduled_date" in update_data:
        new_date = update_data["scheduled_date"]
        if new_date != old_scheduled_date:
            is_reschedule = True
            # Preserve original only if this is the first reschedule
            if task.original_scheduled_date is None:
                task.original_scheduled_date = task.scheduled_date

    if "start_time" in update_data and update_data["start_time"] != old_start_time:
        is_reschedule = True
    if "end_time" in update_data and update_data["end_time"] != old_end_time:
        is_reschedule = True

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        old_val = getattr(task, field)
        if old_val != value:
            changes[field] = {
                "old": str(old_val) if old_val is not None else None,
                "new": str(value) if value is not None else None,
            }
        setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)

    # Log appropriate event
    if is_reschedule:
        _log_event(
            db,
            task_id=task.id,
            event_type=models.EventType.rescheduled,
            details={
                "previous_scheduled_date": str(old_scheduled_date),
                "previous_start_time": str(old_start_time) if old_start_time else None,
                "previous_end_time": str(old_end_time) if old_end_time else None,
                "new_scheduled_date": str(task.scheduled_date),
                "new_start_time": str(task.start_time) if task.start_time else None,
                "new_end_time": str(task.end_time) if task.end_time else None,
                "other_changes": {k: v for k, v in changes.items() if k not in ("scheduled_date", "start_time", "end_time")},
            },
        )
    elif changes:
        _log_event(
            db,
            task_id=task.id,
            event_type=models.EventType.updated,
            details={"changes": changes},
        )

    db.commit()
    db.refresh(task)
    return task


def reschedule_task(
    db: Session,
    task: models.Task,
    payload: schemas.TaskReschedule,
) -> models.Task:
    """Explicitly reschedule a task's date and times."""
    old_scheduled_date = task.scheduled_date
    old_start_time = task.start_time
    old_end_time = task.end_time

    if task.original_scheduled_date is None:
        task.original_scheduled_date = task.scheduled_date

    task.scheduled_date = payload.scheduled_date
    task.start_time = payload.start_time
    task.end_time = payload.end_time
    task.updated_at = datetime.now(timezone.utc)

    _log_event(
        db,
        task_id=task.id,
        event_type=models.EventType.rescheduled,
        details={
            "previous_scheduled_date": str(old_scheduled_date),
            "previous_start_time": str(old_start_time) if old_start_time else None,
            "previous_end_time": str(old_end_time) if old_end_time else None,
            "new_scheduled_date": str(task.scheduled_date),
            "new_start_time": str(task.start_time) if task.start_time else None,
            "new_end_time": str(task.end_time) if task.end_time else None,
        },
    )

    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task: models.Task) -> models.Task:
    """Mark a task as completed and log a completed event."""
    now = datetime.now(timezone.utc)
    task.status = models.TaskStatus.completed.value
    task.completed_at = now
    task.updated_at = now

    _log_event(
        db,
        task_id=task.id,
        event_type=models.EventType.completed,
        details={"completed_at": now.isoformat()},
    )

    db.commit()
    db.refresh(task)
    return task


def reopen_task(db: Session, task: models.Task) -> models.Task:
    """Reopen a completed task: set status to pending, clear completed_at, and log reopened event."""
    now = datetime.now(timezone.utc)
    previous_completed_at = task.completed_at.isoformat() if task.completed_at else None

    task.status = models.TaskStatus.pending.value
    task.completed_at = None
    task.updated_at = now

    _log_event(
        db,
        task_id=task.id,
        event_type=models.EventType.reopened,
        details={
            "reopened_at": now.isoformat(),
            "previous_completed_at": previous_completed_at,
        },
    )

    db.commit()
    db.refresh(task)
    return task


def soft_delete_task(db: Session, task: models.Task) -> models.Task:
    """Soft-delete a task and log a deleted event."""
    now = datetime.now(timezone.utc)
    task.deleted_at = now
    task.updated_at = now

    _log_event(
        db,
        task_id=task.id,
        event_type=models.EventType.deleted,
        details={"deleted_at": now.isoformat()},
    )

    db.commit()
    db.refresh(task)
    return task


def get_task_history(db: Session, task_id: int) -> List[models.TaskEvent]:
    """Retrieve all activity events for a task ordered chronologically."""
    stmt = (
        select(models.TaskEvent)
        .where(models.TaskEvent.task_id == task_id)
        .order_by(models.TaskEvent.event_timestamp.asc(), models.TaskEvent.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_tasks_by_date(
    db: Session,
    target_date: date,
    include_deleted: bool = True,
) -> List[models.Task]:
    """
    Retrieve all tasks associated with target_date.
    Matches tasks where:
      - scheduled_date == target_date OR
      - original_scheduled_date == target_date
    Ordered chronologically by start_time (nulls last), then id.
    """
    stmt = select(models.Task).where(
        or_(
            models.Task.scheduled_date == target_date,
            models.Task.original_scheduled_date == target_date,
        )
    )
    if not include_deleted:
        stmt = stmt.where(models.Task.deleted_at.is_(None))

    # Order: tasks with start_time first in ascending order, then tasks without start_time, then id
    stmt = stmt.order_by(
        models.Task.start_time.is_(None),
        models.Task.start_time.asc(),
        models.Task.id.asc(),
    )
    return list(db.scalars(stmt).all())


# --------------------------------------------------------------------------- #
# Analytics (Stage 4)
# --------------------------------------------------------------------------- #

KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def _to_kolkata_date(dt: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KOLKATA_TZ).date()


def get_analytics(db: Session, days: int = 84) -> dict:
    """
    Compute comprehensive productivity analytics based on real task data.
    Uses Asia/Kolkata timezone for daily reporting boundaries.
    """
    now_kolkata = datetime.now(KOLKATA_TZ)
    today_date = now_kolkata.date()
    today_str = today_date.isoformat()
    reported_at = now_kolkata.isoformat()

    # Get all active (non-deleted) tasks
    stmt = select(models.Task).where(models.Task.deleted_at.is_(None))
    tasks = list(db.scalars(stmt).all())

    # Summary metrics
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == models.TaskStatus.completed.value)
    pending = sum(1 for t in tasks if t.status == models.TaskStatus.pending.value)

    # Overdue: pending and (scheduled_date < today_date or (scheduled_date == today_date and end_time < now))
    overdue = sum(
        1 for t in tasks
        if t.status == models.TaskStatus.pending.value
        and (
            t.scheduled_date < today_date
            or (t.scheduled_date == today_date and t.end_time is not None and t.end_time < now_kolkata.time())
        )
    )
    completion_percentage = round((completed / total * 100), 1) if total > 0 else 0.0

    # Today's daily metric
    today_tasks = [t for t in tasks if t.scheduled_date == today_date]
    today_total = len(today_tasks)
    today_completed = sum(1 for t in today_tasks if t.status == models.TaskStatus.completed.value)
    today_pending = sum(1 for t in today_tasks if t.status == models.TaskStatus.pending.value)
    today_pct = round((today_completed / today_total * 100), 1) if today_total > 0 else 0.0

    today_metric = {
        "date": today_str,
        "day_name": today_date.strftime("%a"),
        "total": today_total,
        "completed": today_completed,
        "pending": today_pending,
        "completion_percentage": today_pct,
    }

    # 7-day trend (last 7 days ending today)
    seven_day_trend = []
    for i in reversed(range(7)):
        d = today_date - timedelta(days=i)
        d_tasks = [t for t in tasks if t.scheduled_date == d]
        d_tot = len(d_tasks)
        d_comp = sum(1 for t in d_tasks if t.status == models.TaskStatus.completed.value)
        d_pend = sum(1 for t in d_tasks if t.status == models.TaskStatus.pending.value)
        d_pct = round((d_comp / d_tot * 100), 1) if d_tot > 0 else 0.0
        seven_day_trend.append({
            "date": d.isoformat(),
            "day_name": d.strftime("%a"),
            "total": d_tot,
            "completed": d_comp,
            "pending": d_pend,
            "completion_percentage": d_pct,
        })

    # Productivity heatmap for specified days (default 84 days = 12 weeks)
    completed_by_date: Dict[date, int] = {}
    scheduled_by_date: Dict[date, int] = {}

    for t in tasks:
        scheduled_by_date[t.scheduled_date] = scheduled_by_date.get(t.scheduled_date, 0) + 1
        if t.status == models.TaskStatus.completed.value:
            if t.completed_at:
                c_date = _to_kolkata_date(t.completed_at)
            else:
                c_date = t.scheduled_date
            completed_by_date[c_date] = completed_by_date.get(c_date, 0) + 1

    # Also capture task completion history events for comprehensive history
    event_stmt = select(models.TaskEvent).where(
        models.TaskEvent.event_type == models.EventType.completed.value
    )
    completed_events = list(db.scalars(event_stmt).all())
    event_completed_by_date: Dict[date, set[int]] = {}
    for ev in completed_events:
        ev_date = _to_kolkata_date(ev.event_timestamp)
        if ev_date not in event_completed_by_date:
            event_completed_by_date[ev_date] = set()
        event_completed_by_date[ev_date].add(ev.task_id)

    heatmap = []
    for i in reversed(range(days)):
        d = today_date - timedelta(days=i)
        comp_count = max(
            completed_by_date.get(d, 0),
            len(event_completed_by_date.get(d, set()))
        )
        tot_sched = scheduled_by_date.get(d, 0)

        if comp_count == 0:
            intensity = 0
        elif comp_count == 1:
            intensity = 1
        elif comp_count == 2:
            intensity = 2
        elif comp_count <= 4:
            intensity = 3
        else:
            intensity = 4

        heatmap.append({
            "date": d.isoformat(),
            "completed_count": comp_count,
            "total_scheduled": tot_sched,
            "intensity": intensity,
        })

    # Category breakdown
    category_breakdown = []
    for cat in models.Category:
        cat_val = cat.value
        cat_tasks = [t for t in tasks if t.category == cat_val]
        c_tot = len(cat_tasks)
        c_comp = sum(1 for t in cat_tasks if t.status == models.TaskStatus.completed.value)
        c_pend = sum(1 for t in cat_tasks if t.status == models.TaskStatus.pending.value)
        category_breakdown.append({
            "category": cat_val,
            "total": c_tot,
            "completed": c_comp,
            "pending": c_pend,
        })

    # Priority breakdown
    priority_breakdown = []
    for prio in models.Priority:
        prio_val = prio.value
        prio_tasks = [t for t in tasks if t.priority == prio_val]
        p_tot = len(prio_tasks)
        p_comp = sum(1 for t in prio_tasks if t.status == models.TaskStatus.completed.value)
        p_pend = sum(1 for t in prio_tasks if t.status == models.TaskStatus.pending.value)
        priority_breakdown.append({
            "priority": prio_val,
            "total": p_tot,
            "completed": p_comp,
            "pending": p_pend,
        })

    return {
        "timezone": "Asia/Kolkata",
        "reported_at": reported_at,
        "today_date": today_str,
        "summary": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_percentage": completion_percentage,
        },
        "today": today_metric,
        "seven_day_trend": seven_day_trend,
        "heatmap": heatmap,
        "category_breakdown": category_breakdown,
        "priority_breakdown": priority_breakdown,
    }

