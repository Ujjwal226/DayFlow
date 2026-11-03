import uuid
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.task import Task


class CategoryRepository:
    """Database repository for categories strictly isolated by user."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_normalized_name(self, name_normalized: str, user_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(
            Category.name_normalized == name_normalized,
            Category.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: uuid.UUID) -> List[Category]:
        stmt = (
            select(Category)
            .where(Category.user_id == user_id)
            .order_by(Category.name.asc(), Category.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_task_count(self, category_id: uuid.UUID, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(Task.id))
            .where(
                Task.category_id == category_id,
                Task.user_id == user_id,
                Task.is_archived.is_(False),
            )
        )
        return self.db.execute(stmt).scalar() or 0

    def get_task_counts_map(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        stmt = (
            select(Task.category_id, func.count(Task.id))
            .where(
                Task.user_id == user_id,
                Task.category_id.isnot(None),
                Task.is_archived.is_(False),
            )
            .group_by(Task.category_id)
        )
        rows = self.db.execute(stmt).all()
        return {cat_id: count for cat_id, count in rows if cat_id is not None}

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

