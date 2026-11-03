import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreateRequest, TagResponse, TagUpdateRequest


class TagService:
    """Service handling business logic and user isolation for reusable tags."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TagRepository(db)

    def list_tags(self, user_id: uuid.UUID) -> List[TagResponse]:
        tags = self.repo.list_by_user(user_id)
        counts_map = self.repo.get_task_counts_map(user_id)
        results = []
        for tag in tags:
            res = TagResponse.model_validate(tag)
            res.task_count = counts_map.get(tag.id, 0)
            results.append(res)
        return results

    def get_tag(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> TagResponse:
        tag = self.repo.get_by_id(tag_id, user_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found.",
            )
        counts_map = self.repo.get_task_counts_map(user_id)
        res = TagResponse.model_validate(tag)
        res.task_count = counts_map.get(tag.id, 0)
        return res

    def create_tag(self, user_id: uuid.UUID, payload: TagCreateRequest) -> TagResponse:
        normalized = payload.name.lower()
        existing = self.repo.get_by_normalized_name(normalized, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{payload.name}' already exists.",
            )

        tag = Tag(
            user_id=user_id,
            name=payload.name,
            name_normalized=normalized,
            color=payload.color,
        )
        created = self.repo.create(tag)
        res = TagResponse.model_validate(created)
        res.task_count = 0
        return res

    def update_tag(
        self,
        tag_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: TagUpdateRequest,
    ) -> TagResponse:
        tag = self.repo.get_by_id(tag_id, user_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found.",
            )

        if payload.name is not None:
            new_normalized = payload.name.lower()
            if new_normalized != tag.name_normalized:
                existing = self.repo.get_by_normalized_name(new_normalized, user_id)
                if existing and existing.id != tag_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Tag with name '{payload.name}' already exists.",
                    )
                tag.name = payload.name
                tag.name_normalized = new_normalized

        if payload.color is not None:
            tag.color = payload.color

        updated = self.repo.update(tag)
        counts_map = self.repo.get_task_counts_map(user_id)
        res = TagResponse.model_validate(updated)
        res.task_count = counts_map.get(tag.id, 0)
        return res

    def delete_tag(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> None:
        tag = self.repo.get_by_id(tag_id, user_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found.",
            )
        # Deleting tag removes task associations without deleting tasks
        self.repo.delete(tag)

