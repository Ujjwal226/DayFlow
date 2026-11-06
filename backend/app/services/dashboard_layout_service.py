import uuid
from typing import List
from sqlalchemy.orm import Session

from app.core.dashboard_registry import get_default_dashboard_widgets
from app.repositories.dashboard_layout_repository import DashboardLayoutRepository
from app.schemas.dashboard import (
    DashboardLayoutResponse,
    DashboardLayoutUpdateRequest,
    DashboardWidgetItemSchema,
)


class DashboardLayoutService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DashboardLayoutRepository(db)

    def get_layout(self, user_id: uuid.UUID) -> DashboardLayoutResponse:
        """
        Retrieves the user's dashboard layout.
        If the user has not customized their layout, returns the default layout
        without inserting a row into the database.
        """
        layout = self.repository.get_by_user_id(user_id)
        if layout is None:
            default_widgets = get_default_dashboard_widgets()
            return DashboardLayoutResponse(
                id=None,
                user_id=user_id,
                widgets=[DashboardWidgetItemSchema(**w) for w in default_widgets],
                is_customized=False,
                created_at=None,
                updated_at=None,
            )

        # Sort widgets by order before returning
        sorted_widgets = sorted(layout.widgets, key=lambda w: w.get("order", 0))
        return DashboardLayoutResponse(
            id=layout.id,
            user_id=layout.user_id,
            widgets=[DashboardWidgetItemSchema(**w) for w in sorted_widgets],
            is_customized=True,
            created_at=layout.created_at,
            updated_at=layout.updated_at,
        )

    def update_layout(
        self, user_id: uuid.UUID, update_data: DashboardLayoutUpdateRequest
    ) -> DashboardLayoutResponse:
        """
        Persists a full replacement of the user's dashboard layout configuration.
        """
        # Sort items by order for canonical persistence
        sorted_items = sorted(update_data.widgets, key=lambda item: item.order)
        serialized_widgets = [
            {
                "widget_id": item.widget_id.value,
                "is_visible": item.is_visible,
                "order": item.order,
                "size": item.size.value,
            }
            for item in sorted_items
        ]

        layout = self.repository.create_or_update(user_id, serialized_widgets)
        self.db.commit()
        self.db.refresh(layout)

        return DashboardLayoutResponse(
            id=layout.id,
            user_id=layout.user_id,
            widgets=[DashboardWidgetItemSchema(**w) for w in layout.widgets],
            is_customized=True,
            created_at=layout.created_at,
            updated_at=layout.updated_at,
        )

    def reset_layout(self, user_id: uuid.UUID) -> DashboardLayoutResponse:
        """
        Deletes the user's customized layout from the database and returns the default layout.
        """
        self.repository.delete_by_user_id(user_id)
        self.db.commit()

        default_widgets = get_default_dashboard_widgets()
        return DashboardLayoutResponse(
            id=None,
            user_id=user_id,
            widgets=[DashboardWidgetItemSchema(**w) for w in default_widgets],
            is_customized=False,
            created_at=None,
            updated_at=None,
        )

