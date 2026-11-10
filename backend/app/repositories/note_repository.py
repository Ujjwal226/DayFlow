import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.note import Note, NoteTag
from app.models.tag import Tag


class NoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, note_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Note]:
        """Fetch a single note strictly scoped to the user with eager relationships."""
        stmt = (
            select(Note)
            .where(Note.id == note_id, Note.user_id == user_id)
            .options(
                selectinload(Note.category),
                selectinload(Note.project),
                selectinload(Note.task),
                selectinload(Note.tags),
            )
        )
        return self.db.scalars(stmt).first()

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
    ) -> Tuple[List[Note], int]:
        """List notes scoped to user with flexible filters and total count."""
        base_query = select(Note).where(Note.user_id == user_id)

        if is_archived is not None:
            base_query = base_query.where(Note.is_archived == is_archived)

        if is_pinned is not None:
            base_query = base_query.where(Note.is_pinned == is_pinned)

        if category_id is not None:
            base_query = base_query.where(Note.category_id == category_id)

        if project_id is not None:
            base_query = base_query.where(Note.project_id == project_id)

        if task_id is not None:
            base_query = base_query.where(Note.task_id == task_id)

        if tag_id is not None:
            base_query = base_query.join(Note.tags).where(Tag.id == tag_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    Note.title.ilike(term),
                    Note.content.ilike(term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Order: pinned first, then updated_at descending
        stmt = (
            base_query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(
                selectinload(Note.category),
                selectinload(Note.project),
                selectinload(Note.task),
                selectinload(Note.tags),
            )
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(self, note: Note) -> Note:
        self.db.add(note)
        self.db.flush()
        return note

    def delete(self, note: Note) -> None:
        self.db.delete(note)
        self.db.flush()

    def set_tags(self, note: Note, tags: List[Tag]) -> None:
        note.tags = tags
        self.db.flush()

