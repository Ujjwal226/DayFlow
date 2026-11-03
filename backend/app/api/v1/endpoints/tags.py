import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreateRequest, TagResponse, TagUpdateRequest
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    """Create a new reusable tag for the authenticated user."""
    service = TagService(db)
    return service.create_tag(user_id=current_user.id, payload=payload)


@router.get("", response_model=List[TagResponse])
def list_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TagResponse]:
    """List all tags belonging to the authenticated user with task counts."""
    service = TagService(db)
    return service.list_tags(user_id=current_user.id)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    """Retrieve details of a single tag."""
    service = TagService(db)
    return service.get_tag(tag_id=tag_id, user_id=current_user.id)


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    """Update name or color of a tag."""
    service = TagService(db)
    return service.update_tag(tag_id=tag_id, user_id=current_user.id, payload=payload)


@router.delete("/{tag_id}", status_code=status.HTTP_200_OK)
def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a tag. Removes associations from tasks without deleting tasks."""
    service = TagService(db)
    service.delete_tag(tag_id=tag_id, user_id=current_user.id)
    return {"message": "Tag deleted successfully."}

