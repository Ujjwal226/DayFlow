import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dashboard_layout import DashboardLayout


class DashboardLayoutRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[DashboardLayout]:
        stmt = select(DashboardLayout).where(DashboardLayout.user_id == user_id)
        return self.db.scalars(stmt).first()

    def create_or_update(
        self, user_id: uuid.UUID, widgets_data: List[Dict[str, Any]]
    ) -> DashboardLayout:
        layout = self.get_by_user_id(user_id)
        if layout is None:
            layout = DashboardLayout(
                user_id=user_id,
                widgets=widgets_data,
            )
            self.db.add(layout)
        else:
            layout.widgets = widgets_data
        self.db.flush()
        return layout

    def delete_by_user_id(self, user_id: uuid.UUID) -> bool:
        layout = self.get_by_user_id(user_id)
        if layout is not None:
            self.db.delete(layout)
            self.db.flush()
            return True
        return False

