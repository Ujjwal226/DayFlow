"""
DayFlow backend – tasks router.

Endpoints
---------
POST   /tasks
GET    /tasks
GET    /tasks/{task_id}
PUT    /tasks/{task_id}
DELETE /tasks/{task_id}
PATCH  /tasks/{task_id}/complete
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task_or_404(task_id: int, db: Session) -> "crud.models.Task":
    task = crud.get_task(db, task_id)
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
# Retrieve
# --------------------------------------------------------------------------- #

@router.get(
    "/{task_id}",
    response_model=schemas.TaskResponse,
    summary="Get a single task by ID",
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(task_id, db)


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
