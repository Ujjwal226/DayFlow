import uuid
from datetime import date, datetime
from typing import Annotated, List, Literal, Optional, Union
import zoneinfo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.task import TaskPriority, TaskStatus
from app.schemas.category import CategoryResponse
from app.schemas.project import ProjectResponse


def validate_iana_timezone(v: Optional[str]) -> str:
    tz_str = v.strip() if v else "UTC"
    try:
        zoneinfo.ZoneInfo(tz_str)
    except Exception:
        raise ValueError(f"Invalid IANA timezone identifier: '{tz_str}'")
    return tz_str


# ---------------------------------------------------------
# Standalone Calendar Event Item
# ---------------------------------------------------------

class CalendarLinkedTaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None


class CalendarEventItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: Literal["event"] = "event"
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    color: Optional[str] = None
    is_all_day: bool
    timezone: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    task_id: Optional[uuid.UUID] = None
    task: Optional[CalendarLinkedTaskSummary] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------
# Task Deadline Item
# ---------------------------------------------------------

class CalendarTaskDeadlineItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: Literal["task_deadline"] = "task_deadline"
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    start_date: Optional[datetime] = None
    due_date: datetime
    project_id: Optional[uuid.UUID] = None
    project: Optional[ProjectResponse] = None
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryResponse] = None
    recurring_task_id: Optional[uuid.UUID] = None
    occurrence_date: Optional[date] = None
    occurrence_index: Optional[int] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime


# Discriminated union of calendar feed items
CalendarFeedItem = Annotated[
    Union[CalendarEventItem, CalendarTaskDeadlineItem],
    Field(discriminator="type"),
]


# ---------------------------------------------------------
# Unified Feed Response
# ---------------------------------------------------------

class CalendarFeedResponse(BaseModel):
    items: List[CalendarFeedItem]
    range_start: datetime
    range_end: datetime
    timezone: str
    total: int


# ---------------------------------------------------------
# Task Scheduling Request
# ---------------------------------------------------------

class ScheduleTaskRequest(BaseModel):
    task_id: uuid.UUID = Field(..., description="UUID of existing task to schedule")
    start_at: datetime = Field(..., description="UTC start datetime for time block")
    end_at: datetime = Field(..., description="UTC end datetime for time block")
    timezone: str = Field("UTC", max_length=50, description="IANA timezone identifier")
    title: Optional[str] = Field(None, max_length=200, description="Optional custom title; defaults to task title")
    description: Optional[str] = Field(None, max_length=5000, description="Optional custom description")
    color: Optional[str] = Field(None, max_length=50, description="Optional color code")
    location: Optional[str] = Field(None, max_length=255, description="Optional location or meeting link")

    @field_validator("title")
    @classmethod
    def validate_title_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                return None
            return trimmed
        return None

    @field_validator("timezone")
    @classmethod
    def check_tz(cls, v: str) -> str:
        return validate_iana_timezone(v)

    @model_validator(mode="after")
    def validate_time_range(self) -> "ScheduleTaskRequest":
        if self.end_at <= self.start_at:
            raise ValueError("Timed event 'end_at' must be strictly after 'start_at'.")
        return self

