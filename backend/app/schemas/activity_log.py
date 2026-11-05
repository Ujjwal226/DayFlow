import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.activity_log import ActivityAction, ActivityEntityType


class ActivityChangeValue(BaseModel):
    old: Optional[Any] = None
    new: Optional[Any] = None


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    recurring_task_id: Optional[uuid.UUID] = None
    entity_type: ActivityEntityType
    entity_id: uuid.UUID
    action: ActivityAction
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ActivityLogListResponse(BaseModel):
    items: List[ActivityLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
