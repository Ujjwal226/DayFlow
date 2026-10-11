"""
DayFlow backend – CRUD helpers.

All database operations live here so routers stay thin.
Business logic (e.g. setting completed_at, logging task events) lives here.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
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
