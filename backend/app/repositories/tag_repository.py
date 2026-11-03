import uuid
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tag import Tag, TaskTag
from app.models.task import Task


class TagRepository:
    """Database repository for tags strictly isolated by user."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Tag]:
        stmt = select(Tag).where(
            Tag.id == tag_id,
            Tag.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_normalized_name(self, name_normalized: str, user_id: uuid.UUID) -> Optional[Tag]:
        stmt = select(Tag).where(
            Tag.name_normalized == name_normalized,
            Tag.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: uuid.UUID) -> List[Tag]:
        stmt = (
            select(Tag)
            .where(Tag.user_id == user_id)
            .order_by(Tag.name.asc(), Tag.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_ids(self, tag_ids: List[uuid.UUID], user_id: uuid.UUID) -> List[Tag]:
        if not tag_ids:
            return []
        stmt = select(Tag).where(
            Tag.id.in_(tag_ids),
            Tag.user_id == user_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_task_counts_map(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        stmt = (
            select(TaskTag.tag_id, func.count(Task.id))
            .join(Task, Task.id == TaskTag.task_id)
            .where(
                Task.user_id == user_id,
                Task.is_archived.is_(False),
            )
            .group_by(TaskTag.tag_id)
        )
        rows = self.db.execute(stmt).all()
        return {tag_id: count for tag_id, count in rows if tag_id is not None}

    def create(self, tag: Tag) -> Tag:
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag: Tag) -> Tag:
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag: Tag) -> None:
        self.db.delete(tag)
        self.db.commit()

