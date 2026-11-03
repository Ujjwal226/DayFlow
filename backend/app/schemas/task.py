import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.task import TaskPriority, TaskStatus


class TaskCreateRequest(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=10000, description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Initial task status")
    start_date: Optional[datetime] = Field(None, description="Task start time in UTC")
    due_date: Optional[datetime] = Field(None, description="Task deadline in UTC")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Task title cannot be empty or whitespace only.")
        if len(trimmed) > 200:
            raise ValueError("Task title cannot exceed 200 characters.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskCreateRequest":
        if self.start_date and self.due_date:
            if self.due_date < self.start_date:
                raise ValueError("Due date cannot be earlier than start date.")
        return self


class TaskUpdateRequest(BaseModel):
    """Schema for partial task updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated task title")
    description: Optional[str] = Field(None, max_length=10000, description="Updated description")
    priority: Optional[TaskPriority] = Field(None, description="Updated priority")
    status: Optional[TaskStatus] = Field(None, description="Updated status")
    start_date: Optional[datetime] = Field(None, description="Updated start date")
    due_date: Optional[datetime] = Field(None, description="Updated due date")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Task title cannot be empty or whitespace only.")
            if len(trimmed) > 200:
                raise ValueError("Task title cannot exceed 200 characters.")
            return trimmed
        return None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskUpdateRequest":
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date cannot be earlier than start date.")
        return self


class TaskResponse(BaseModel):
    """Schema representing a task returned from the API."""
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_archived: bool
    is_overdue: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskStatisticsResponse(BaseModel):
    """Aggregated task statistics for the authenticated user."""
    total: int
    todo: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int
    upcoming: int

