"""
DayFlow backend – CRUD helpers.

All database operations live here so routers stay thin.
Business logic (e.g. setting completed_at) also lives here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


# --------------------------------------------------------------------------- #
# Task CRUD
# --------------------------------------------------------------------------- #

def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    """Return a task by ID only if it has not been soft-deleted."""
    stmt = (
        select(models.Task)
        .where(models.Task.id == task_id)
        .where(models.Task.deleted_at.is_(None))
    )
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
    count_stmt = stmt.with_only_columns(  # type: ignore[call-arg]
        models.Task.id
    ).order_by(None)
    total = len(db.scalars(count_stmt).all())

    stmt = stmt.order_by(models.Task.scheduled_date, models.Task.id).offset(skip).limit(limit)
    tasks = list(db.scalars(stmt).all())
    return tasks, total


def create_task(db: Session, payload: schemas.TaskCreate) -> models.Task:
    """Create a new task, preserving the original_scheduled_date."""
    data = payload.model_dump()
    task = models.Task(
        **data,
        original_scheduled_date=data["scheduled_date"],
        status=models.TaskStatus.pending.value,
    )
    db.add(task)
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

    If scheduled_date changes and original_scheduled_date was never set,
    keep the original preserved.
    """
    update_data = payload.model_dump(exclude_none=True)

    if "scheduled_date" in update_data:
        # Preserve original only if this is the first reschedule
        if task.original_scheduled_date is None:
            task.original_scheduled_date = task.scheduled_date

    for field, value in update_data.items():
        # Convert enum instances to their string values for ORM columns
        if hasattr(value, "value"):
            value = value.value
        setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task: models.Task) -> models.Task:
    """Mark a task as completed."""
    now = datetime.now(timezone.utc)
    task.status = models.TaskStatus.completed.value
    task.completed_at = now
    task.updated_at = now
    db.commit()
    db.refresh(task)
    return task


def soft_delete_task(db: Session, task: models.Task) -> models.Task:
    """Soft-delete a task by setting deleted_at."""
    now = datetime.now(timezone.utc)
    task.deleted_at = now
    task.updated_at = now
    db.commit()
    db.refresh(task)
    return task
