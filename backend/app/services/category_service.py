import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest


class CategoryService:
    """Service handling business logic and user isolation for categories."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    def list_categories(self, user_id: uuid.UUID) -> List[CategoryResponse]:
        categories = self.repo.list_by_user(user_id)
        counts_map = self.repo.get_task_counts_map(user_id)
        results = []
        for cat in categories:
            res = CategoryResponse.model_validate(cat)
            res.task_count = counts_map.get(cat.id, 0)
            results.append(res)
        return results

    def get_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> CategoryResponse:
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        res = CategoryResponse.model_validate(category)
        res.task_count = self.repo.get_task_count(category_id, user_id)
        return res

    def create_category(self, user_id: uuid.UUID, payload: CategoryCreateRequest) -> CategoryResponse:
        normalized = payload.name.lower()
        existing = self.repo.get_by_normalized_name(normalized, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{payload.name}' already exists.",
            )

        category = Category(
            user_id=user_id,
            name=payload.name,
            name_normalized=normalized,
            description=payload.description,
            color=payload.color,
            icon=payload.icon,
        )
        created = self.repo.create(category)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                entity_type=ActivityEntityType.CATEGORY.value,
                entity_id=created.id,
                action=ActivityAction.CATEGORY_CREATED.value,
                changes=None,
                extra_metadata={"name": created.name},
            ),
            commit=False,
        )

        res = CategoryResponse.model_validate(created)
        res.task_count = 0
        return res

    def update_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CategoryUpdateRequest,
    ) -> CategoryResponse:
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )

        changes = {}
        old_name = category.name
        old_desc = category.description
        old_color = category.color
        old_icon = category.icon

        if payload.name is not None:
            new_normalized = payload.name.lower()
            if new_normalized != category.name_normalized:
                existing = self.repo.get_by_normalized_name(new_normalized, user_id)
                if existing and existing.id != category_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Category with name '{payload.name}' already exists.",
                    )
                changes["name"] = {"old": old_name, "new": payload.name}
                category.name = payload.name
                category.name_normalized = new_normalized

        if payload.description is not None and payload.description != old_desc:
            changes["description"] = {"old": old_desc, "new": payload.description}
            category.description = payload.description
        if payload.color is not None and payload.color != old_color:
            changes["color"] = {"old": old_color, "new": payload.color}
            category.color = payload.color
        if payload.icon is not None and payload.icon != old_icon:
            changes["icon"] = {"old": old_icon, "new": payload.icon}
            category.icon = payload.icon

        updated = self.repo.update(category)

        if changes:
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    entity_type=ActivityEntityType.CATEGORY.value,
                    entity_id=updated.id,
                    action=ActivityAction.CATEGORY_UPDATED.value,
                    changes=changes,
                    extra_metadata={"name": updated.name},
                ),
                commit=False,
            )

        res = CategoryResponse.model_validate(updated)
        res.task_count = self.repo.get_task_count(category_id, user_id)
        return res

    def delete_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        # Log deletion before removing
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                entity_type=ActivityEntityType.CATEGORY.value,
                entity_id=category.id,
                action=ActivityAction.CATEGORY_DELETED.value,
                changes=None,
                extra_metadata={"name": category.name},
            ),
            commit=False,
        )

        # Deleting category leaves tasks uncategorized thanks to ON DELETE SET NULL
        self.repo.delete(category)

