import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.dashboard_registry import (
    DashboardWidgetId,
    DashboardWidgetSize,
    WIDGET_METADATA,
)


class DashboardWidgetItemSchema(BaseModel):
    widget_id: DashboardWidgetId = Field(..., description="Unique identifier for the widget")
    is_visible: bool = Field(..., description="Whether the widget is displayed on the dashboard")
    order: int = Field(..., ge=0, description="Display order index (0-indexed, non-negative)")
    size: DashboardWidgetSize = Field(..., description="Widget size variant: small, medium, or full")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "widget_id": "welcome",
                "is_visible": True,
                "order": 0,
                "size": "full",
            }
        },
    }


class DashboardLayoutResponse(BaseModel):
    id: Optional[uuid.UUID] = Field(None, description="Layout ID if customized and saved in DB")
    user_id: Optional[uuid.UUID] = Field(None, description="Owner user ID")
    widgets: List[DashboardWidgetItemSchema] = Field(..., description="List of configured widgets")
    is_customized: bool = Field(..., description="True if custom layout stored; False if default")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {
        "from_attributes": True,
    }


class DashboardLayoutUpdateRequest(BaseModel):
    widgets: List[DashboardWidgetItemSchema] = Field(
        ...,
        min_length=len(WIDGET_METADATA),
        max_length=len(WIDGET_METADATA),
        description="Complete list of widget configurations covering all supported widgets exactly once",
    )

    @field_validator("widgets")
    @classmethod
    def validate_widgets_completeness_and_uniqueness(
        cls, widgets: List[DashboardWidgetItemSchema]
    ) -> List[DashboardWidgetItemSchema]:
        seen_ids = set()
        for item in widgets:
            if item.widget_id in seen_ids:
                raise ValueError(f"Duplicate widget_id: '{item.widget_id.value}' is not allowed")
            seen_ids.add(item.widget_id)

        all_supported = set(WIDGET_METADATA.keys())
        missing = all_supported - seen_ids
        if missing:
            missing_names = sorted([w.value for w in missing])
            raise ValueError(f"Missing required widget(s): {', '.join(missing_names)}")

        # Also ensure orders are unique non-negative integers among items
        orders = [item.order for item in widgets]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate display orders are not allowed")

        return widgets

    model_config = {
        "json_schema_extra": {
            "example": {
                "widgets": [
                    {"widget_id": "welcome", "is_visible": True, "order": 0, "size": "full"},
                    {"widget_id": "productivity_overview", "is_visible": True, "order": 1, "size": "full"},
                    {"widget_id": "today_tasks", "is_visible": True, "order": 2, "size": "medium"},
                    {"widget_id": "upcoming_tasks", "is_visible": True, "order": 3, "size": "medium"},
                    {"widget_id": "overdue_tasks", "is_visible": True, "order": 4, "size": "medium"},
                    {"widget_id": "recent_activity", "is_visible": True, "order": 5, "size": "medium"},
                    {"widget_id": "projects_overview", "is_visible": True, "order": 6, "size": "medium"},
                    {"widget_id": "productivity_trends", "is_visible": True, "order": 7, "size": "medium"},
                    {"widget_id": "recurring_insights", "is_visible": True, "order": 8, "size": "medium"},
                    {"widget_id": "quick_actions", "is_visible": True, "order": 9, "size": "full"},
                ]
            }
        }
    }

