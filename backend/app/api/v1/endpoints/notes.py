import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.note import (
    NoteCreateRequest,
    NoteListResponse,
    NoteResponse,
    NoteUpdateRequest,
)
from app.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("", response_model=NoteListResponse)
def list_notes(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search term in title or content"),
    is_pinned: Optional[bool] = Query(default=None, description="Filter by pinned status"),
    is_archived: Optional[bool] = Query(default=False, description="Filter by archived status"),
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter by category ID"),
    project_id: Optional[uuid.UUID] = Query(default=None, description="Filter by project ID"),
    task_id: Optional[uuid.UUID] = Query(default=None, description="Filter by task ID"),
    tag_id: Optional[uuid.UUID] = Query(default=None, description="Filter by tag ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteListResponse:
    """Retrieve paginated notes for the authenticated user."""
    service = NoteService(db)
    return service.list_notes(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        is_pinned=is_pinned,
        is_archived=is_archived,
        category_id=category_id,
        project_id=project_id,
        task_id=task_id,
        tag_id=tag_id,
    )


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    """Create a new note owned strictly by the authenticated user."""
    service = NoteService(db)
    return service.create_note(user_id=current_user.id, payload=payload)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    """Get a specific note by ID."""
    service = NoteService(db)
    return service.get_note(note_id=note_id, user_id=current_user.id)


@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    """Update note details, pinning, archiving, or associated entities."""
    service = NoteService(db)
    return service.update_note(note_id=note_id, user_id=current_user.id, payload=payload)


@router.delete("/{note_id}", response_model=MessageResponse)
def delete_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Permanently delete a note."""
    service = NoteService(db)
    service.delete_note(note_id=note_id, user_id=current_user.id)
    return MessageResponse(message="Note deleted successfully.")

