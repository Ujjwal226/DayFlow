"""
DayFlow backend – tasks router.

Endpoints
---------
POST   /tasks
GET    /tasks
GET    /tasks/history/date/{target_date}
GET    /tasks/{task_id}
PUT    /tasks/{task_id}
DELETE /tasks/{task_id}
PATCH  /tasks/{task_id}/complete
PATCH  /tasks/{task_id}/reopen
PATCH  /tasks/{task_id}/reschedule
GET    /tasks/{task_id}/history
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task_or_404(task_id: int, db: Session, include_deleted: bool = False) -> "crud.models.Task":
    task = crud.get_task(db, task_id, include_deleted=include_deleted)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #

@router.post(
    "",
    response_model=schemas.TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
):
    return crud.create_task(db, payload)


# --------------------------------------------------------------------------- #
# List
# --------------------------------------------------------------------------- #

@router.get(
    "",
    response_model=schemas.TaskListResponse,
    summary="List tasks (excludes deleted)",
)
def list_tasks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
):
    tasks, total = crud.get_tasks(
        db,
        skip=skip,
        limit=limit,
        status=status,
        category=category,
        priority=priority,
    )
    return schemas.TaskListResponse(tasks=tasks, total=total)


# --------------------------------------------------------------------------- #
# Historical tasks by date (Must precede /{task_id} to avoid route collision)
# --------------------------------------------------------------------------- #

@router.get(
    "/history/date/{target_date}",
    response_model=List[schemas.TaskResponse],
    summary="Get tasks for a specific date (scheduled or originally scheduled, including deleted)",
)
def get_tasks_history_by_date(
    target_date: date,
    include_deleted: bool = Query(True, description="Include soft-deleted tasks in historical view"),
    db: Session = Depends(get_db),
):
    return crud.get_tasks_by_date(db, target_date=target_date, include_deleted=include_deleted)


# --------------------------------------------------------------------------- #
# Retrieve single task
# --------------------------------------------------------------------------- #

@router.get(
    "/{task_id}",
    response_model=schemas.TaskResponse,
    summary="Get a single task by ID",
)
def get_task(
    task_id: int,
    include_deleted: bool = Query(False, description="Whether to include soft-deleted task"),
    db: Session = Depends(get_db),
):
    return _get_task_or_404(task_id, db, include_deleted=include_deleted)


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #

@router.put(
    "/{task_id}",
    response_model=schemas.TaskResponse,
    summary="Update a task",
)
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    return crud.update_task(db, task, payload)


# --------------------------------------------------------------------------- #
# Complete
# --------------------------------------------------------------------------- #

@router.patch(
    "/{task_id}/complete",
    response_model=schemas.TaskResponse,
    summary="Mark a task as completed",
)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    if task.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already completed",
        )
    return crud.complete_task(db, task)


# --------------------------------------------------------------------------- #
# Reopen
# --------------------------------------------------------------------------- #

@router.patch(
    "/{task_id}/reopen",
    response_model=schemas.TaskResponse,
    summary="Reopen a completed task",
)
def reopen_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    if task.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already pending",
        )
    return crud.reopen_task(db, task)


# --------------------------------------------------------------------------- #
# Reschedule
# --------------------------------------------------------------------------- #

@router.patch(
    "/{task_id}/reschedule",
    response_model=schemas.TaskResponse,
    summary="Reschedule a task's date and times",
)
def reschedule_task(
    task_id: int,
    payload: schemas.TaskReschedule,
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(task_id, db)
    return crud.reschedule_task(db, task, payload)


# --------------------------------------------------------------------------- #
# Activity History
# --------------------------------------------------------------------------- #

@router.get(
    "/{task_id}/history",
    response_model=List[schemas.TaskEventResponse],
    summary="Get activity history log for a task",
)
def get_task_history(task_id: int, db: Session = Depends(get_db)):
    # Task may be soft-deleted, but its history must still be retrievable
    _get_task_or_404(task_id, db, include_deleted=True)
    return crud.get_task_history(db, task_id)


# --------------------------------------------------------------------------- #
# Delete (soft)
# --------------------------------------------------------------------------- #

@router.delete(
    "/{task_id}",
    response_model=schemas.MessageResponse,
    summary="Soft-delete a task",
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    crud.soft_delete_task(db, task)
    return schemas.MessageResponse(message="Task deleted successfully", task_id=task_id)
