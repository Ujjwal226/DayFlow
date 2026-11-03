import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.task import TaskPriority, TaskStatus
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse


class SubtaskProgressResponse(BaseModel):
    """Dynamic progress information for parent tasks."""
    total_subtasks: int = 0
    completed_subtasks: int = 0
    remaining_subtasks: int = 0
    progress_percentage: float = 0.0


class TaskCategoryAssignmentRequest(BaseModel):
    """Schema for assigning or clearing a category on a task."""
    category_id: Optional[uuid.UUID] = Field(None, description="Category UUID or null to uncategorize")


class TaskTagsAssignmentRequest(BaseModel):
    """Schema for assigning a list of tag IDs to a task."""
    tag_ids: List[uuid.UUID] = Field(default_factory=list, description="List of unique tag IDs to assign")


class SubtaskCreateRequest(BaseModel):
    """Schema for creating a subtask under a parent task."""
    title: str = Field(..., min_length=1, max_length=200, description="Subtask title")
    description: Optional[str] = Field(None, max_length=10000, description="Detailed subtask description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Subtask priority")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Initial subtask status")
    due_date: Optional[datetime] = Field(None, description="Subtask deadline in UTC")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Subtask title cannot be empty or whitespace only.")
        if len(trimmed) > 200:
            raise ValueError("Subtask title cannot exceed 200 characters.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None


class SubtaskUpdateRequest(BaseModel):
    """Schema for updating a subtask."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated subtask title")
    description: Optional[str] = Field(None, max_length=10000, description="Updated description")
    priority: Optional[TaskPriority] = Field(None, description="Updated priority")
    status: Optional[TaskStatus] = Field(None, description="Updated status")
    due_date: Optional[datetime] = Field(None, description="Updated due date")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Subtask title cannot be empty or whitespace only.")
            if len(trimmed) > 200:
                raise ValueError("Subtask title cannot exceed 200 characters.")
            return trimmed
        return None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None


class TaskCreateRequest(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=10000, description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Initial task status")
    start_date: Optional[datetime] = Field(None, description="Task start time in UTC")
    due_date: Optional[datetime] = Field(None, description="Task deadline in UTC")
    category_id: Optional[uuid.UUID] = Field(None, description="Optional category UUID")
    project_id: Optional[uuid.UUID] = Field(None, description="Optional project UUID")
    tag_ids: Optional[List[uuid.UUID]] = Field(default=None, description="Optional list of tag UUIDs")

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
    category_id: Optional[uuid.UUID] = Field(None, description="Updated category UUID (set None to remove)")
    project_id: Optional[uuid.UUID] = Field(None, description="Updated project UUID (set None to remove)")
    tag_ids: Optional[List[uuid.UUID]] = Field(None, description="Updated list of tag UUIDs")

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


class SubtaskResponse(BaseModel):
    """Schema representing a subtask."""
    id: uuid.UUID
    user_id: uuid.UUID
    parent_task_id: uuid.UUID
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


class TaskResponse(BaseModel):
    """Schema representing a task returned from the API."""
    id: uuid.UUID
    user_id: uuid.UUID
    parent_task_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryResponse] = None
    project_id: Optional[uuid.UUID] = None
    tags: List[TagResponse] = Field(default_factory=list)
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_archived: bool
    is_overdue: bool
    progress: SubtaskProgressResponse = Field(default_factory=SubtaskProgressResponse)
    subtasks: List[SubtaskResponse] = Field(default_factory=list)
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
