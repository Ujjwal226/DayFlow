import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.task import SubtaskResponse, SubtaskUpdateRequest
from app.services.task_service import TaskService

router = APIRouter(prefix="/subtasks", tags=["Subtasks"])


@router.get("/{subtask_id}", response_model=SubtaskResponse)
def get_subtask(
    subtask_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskResponse:
    """Retrieve details of a single subtask."""
    service = TaskService(db)
    return service.get_subtask(subtask_id=subtask_id, user_id=current_user.id)


@router.patch("/{subtask_id}", response_model=SubtaskResponse)
def update_subtask(
    subtask_id: uuid.UUID,
    payload: SubtaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskResponse:
    """Update title, description, priority, status, or due date of a subtask."""
    service = TaskService(db)
    return service.update_subtask(subtask_id=subtask_id, user_id=current_user.id, payload=payload)


@router.delete("/{subtask_id}", status_code=status.HTTP_200_OK)
def delete_subtask(
    subtask_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a subtask."""
    service = TaskService(db)
    service.delete_subtask(subtask_id=subtask_id, user_id=current_user.id)
    return {"message": "Subtask deleted successfully."}

