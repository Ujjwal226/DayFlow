import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from app.schemas.task import TaskListResponse
from app.services.category_service import CategoryService
from app.services.task_service import TaskService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Create a new custom category for the authenticated user."""
    service = CategoryService(db)
    return service.create_category(user_id=current_user.id, payload=payload)


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CategoryResponse]:
    """List all categories created by the authenticated user with task counts."""
    service = CategoryService(db)
    return service.list_categories(user_id=current_user.id)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Retrieve details of a single category."""
    service = CategoryService(db)
    return service.get_category(category_id=category_id, user_id=current_user.id)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Update name, description, color, or icon of a category."""
    service = CategoryService(db)
    return service.update_category(category_id=category_id, user_id=current_user.id, payload=payload)


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a category. Associated tasks become uncategorized."""
    service = CategoryService(db)
    service.delete_category(category_id=category_id, user_id=current_user.id)
    return {"message": "Category deleted successfully."}


@router.get("/{category_id}/tasks", response_model=TaskListResponse)
def get_category_tasks(
    category_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """View tasks associated with a specific category."""
    # First verify category exists and is owned by current user
    cat_service = CategoryService(db)
    cat_service.get_category(category_id=category_id, user_id=current_user.id)

    task_service = TaskService(db)
    return task_service.list_tasks(
        user_id=current_user.id,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )

