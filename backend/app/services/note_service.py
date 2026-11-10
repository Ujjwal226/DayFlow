import math
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.note import Note
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task
from app.repositories.note_repository import NoteRepository
from app.schemas.note import (
    NoteCreateRequest,
    NoteListResponse,
    NoteResponse,
    NoteUpdateRequest,
)


class NoteService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NoteRepository(db)

    def _validate_associations(
        self,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        tag_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[Tag]:
        """Validate that all associated entities belong strictly to the authenticated user."""
        if category_id is not None:
            cat = self.db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found or does not belong to user.",
                )

        if project_id is not None:
            proj = self.db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if not proj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found or does not belong to user.",
                )

        if task_id is not None:
            task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found or does not belong to user.",
                )

        resolved_tags: List[Tag] = []
        if tag_ids:
            tags = (
                self.db.query(Tag)
                .filter(Tag.id.in_(tag_ids), Tag.user_id == user_id)
                .all()
            )
            if len(tags) != len(set(tag_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tags not found or do not belong to user.",
                )
            resolved_tags = tags

        return resolved_tags

    def list_notes(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = False,
        category_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        tag_id: Optional[uuid.UUID] = None,
    ) -> NoteListResponse:
        items, total = self.repository.list_notes(
            user_id=user_id,
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

        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        return NoteListResponse(
            items=[NoteResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> NoteResponse:
        note = self.repository.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found.",
            )
        return NoteResponse.model_validate(note)

    def create_note(self, user_id: uuid.UUID, payload: NoteCreateRequest) -> NoteResponse:
        tags = self._validate_associations(
            user_id=user_id,
            category_id=payload.category_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            tag_ids=payload.tag_ids,
        )

        note = Note(
            user_id=user_id,
            title=payload.title,
            content=payload.content,
            is_pinned=payload.is_pinned,
            is_archived=False,
            category_id=payload.category_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
        )
        if tags:
            note.tags = tags

        self.repository.create(note)
        self.db.commit()

        # Reload with relationships
        fresh = self.repository.get_by_id(note.id, user_id)
        return NoteResponse.model_validate(fresh)

    def update_note(
        self, note_id: uuid.UUID, user_id: uuid.UUID, payload: NoteUpdateRequest
    ) -> NoteResponse:
        note = self.repository.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found.",
            )

        # Check associations if updating
        tags: Optional[List[Tag]] = None
        if (
            payload.category_id is not None
            or payload.project_id is not None
            or payload.task_id is not None
            or payload.tag_ids is not None
        ):
            tags = self._validate_associations(
                user_id=user_id,
                category_id=payload.category_id,
                project_id=payload.project_id,
                task_id=payload.task_id,
                tag_ids=payload.tag_ids,
            )

        if payload.title is not None:
            note.title = payload.title
        if payload.content is not None:
            note.content = payload.content
        if payload.is_pinned is not None:
            note.is_pinned = payload.is_pinned
        if payload.is_archived is not None:
            note.is_archived = payload.is_archived

        # Explicit None updates for relationships (e.g. detaching)
        update_dict = payload.model_dump(exclude_unset=True)
        if "category_id" in update_dict:
            note.category_id = payload.category_id
        if "project_id" in update_dict:
            note.project_id = payload.project_id
        if "task_id" in update_dict:
            note.task_id = payload.task_id
        if "tag_ids" in update_dict:
            note.tags = tags if tags is not None else []

        self.db.commit()
        fresh = self.repository.get_by_id(note.id, user_id)
        return NoteResponse.model_validate(fresh)

    def delete_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        note = self.repository.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found.",
            )
        self.repository.delete(note)
        self.db.commit()

