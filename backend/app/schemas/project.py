import re
import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.project import ProjectPriority, ProjectStatus

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


class ProjectStatisticsResponse(BaseModel):
    """Dynamically calculated project statistics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    cancelled_tasks: int = 0
    overdue_tasks: int = 0
    completion_percentage: float = 0.0


class ProjectCreateRequest(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=150, description="Project name")
    description: Optional[str] = Field(None, max_length=10000, description="Detailed project description")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNED, description="Initial project status")
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Project priority")
    start_date: Optional[date] = Field(None, description="Planned project start date")
    due_date: Optional[date] = Field(None, description="Planned project completion deadline")
    color: Optional[str] = Field(None, description="Hex color code (e.g., #3B82F6)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Project name cannot be empty or whitespace only.")
        if len(trimmed) > 150:
            raise ValueError("Project name cannot exceed 150 characters.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not HEX_COLOR_REGEX.match(trimmed):
                raise ValueError("Color must be a valid hex code (e.g. #3B82F6).")
            return trimmed.upper()
        return None

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreateRequest":
        if self.start_date and self.due_date:
            if self.due_date < self.start_date:
                raise ValueError("Due date cannot be earlier than start date.")
        return self


class ProjectUpdateRequest(BaseModel):
    """Schema for updating an existing project."""
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="Updated project name")
    description: Optional[str] = Field(None, max_length=10000, description="Updated description")
    status: Optional[ProjectStatus] = Field(None, description="Updated status")
    priority: Optional[ProjectPriority] = Field(None, description="Updated priority")
    start_date: Optional[date] = Field(None, description="Updated start date")
    due_date: Optional[date] = Field(None, description="Updated due date")
    color: Optional[str] = Field(None, description="Updated hex color code")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Project name cannot be empty or whitespace only.")
            if len(trimmed) > 150:
                raise ValueError("Project name cannot exceed 150 characters.")
            return trimmed
        return None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not HEX_COLOR_REGEX.match(trimmed):
                raise ValueError("Color must be a valid hex code (e.g. #3B82F6).")
            return trimmed.upper()
        return None

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdateRequest":
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date cannot be earlier than start date.")
        return self


class ProjectResponse(BaseModel):
    """Schema representing a project returned from the API."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    priority: ProjectPriority
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    color: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    statistics: Optional[ProjectStatisticsResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

