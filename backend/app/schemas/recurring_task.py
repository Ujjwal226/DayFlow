import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.recurring_task import RecurrenceFrequency
from app.models.task import TaskPriority
from app.schemas.category import CategoryResponse


class RecurringTaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Template task title")
    description: Optional[str] = Field(None, max_length=10000, description="Template task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Template task priority")
    category_id: Optional[uuid.UUID] = Field(None, description="Optional category UUID")
    project_id: Optional[uuid.UUID] = Field(None, description="Optional project UUID")

    frequency: RecurrenceFrequency = Field(..., description="Recurrence frequency (DAILY, WEEKLY, MONTHLY, YEARLY, CUSTOM)")
    interval: int = Field(default=1, ge=1, le=365, description="Interval multiplier")

    start_date: date = Field(..., description="Series start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="Optional series termination date")
    max_occurrences: Optional[int] = Field(None, ge=1, le=1000, description="Optional maximum occurrence limit")

    weekdays: Optional[List[int]] = Field(None, description="List of weekdays (0=Mon, 6=Sun) for WEEKLY recurrence")
    day_of_month: Optional[int] = Field(None, ge=-1, le=31, description="Day of month (1-31, or -1 for last day)")
    month_of_year: Optional[int] = Field(None, ge=1, le=12, description="Month of year (1-12) for YEARLY recurrence")
    timezone: Optional[str] = Field(default="UTC", description="Timezone name")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only.")
        return trimmed

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            if not v:
                raise ValueError("Weekdays list cannot be empty when provided.")
            for w in v:
                if w < 0 or w > 6:
                    raise ValueError(f"Invalid weekday: {w}. Must be between 0 (Monday) and 6 (Sunday).")
            return sorted(list(set(v)))
        return None

    @model_validator(mode="after")
    def validate_rules(self) -> "RecurringTaskCreateRequest":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date.")

        if self.frequency == RecurrenceFrequency.WEEKLY and not self.weekdays:
            # Default to the weekday of start_date
            self.weekdays = [self.start_date.weekday()]

        if self.frequency == RecurrenceFrequency.MONTHLY and self.day_of_month is None:
            self.day_of_month = self.start_date.day

        if self.frequency == RecurrenceFrequency.YEARLY:
            if self.month_of_year is None:
                self.month_of_year = self.start_date.month
            if self.day_of_month is None:
                self.day_of_month = self.start_date.day

        return self


class RecurringTaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    priority: Optional[TaskPriority] = Field(None)
    category_id: Optional[uuid.UUID] = Field(None)
    project_id: Optional[uuid.UUID] = Field(None)

    frequency: Optional[RecurrenceFrequency] = Field(None)
    interval: Optional[int] = Field(None, ge=1, le=365)
    end_date: Optional[date] = Field(None)
    max_occurrences: Optional[int] = Field(None, ge=1, le=1000)

    weekdays: Optional[List[int]] = Field(None)
    day_of_month: Optional[int] = Field(None, ge=-1, le=31)
    month_of_year: Optional[int] = Field(None, ge=1, le=12)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Title cannot be empty or whitespace only.")
            return trimmed
        return None


class RecurringTaskSkipRequest(BaseModel):
    skip_date: date = Field(..., description="Date to skip occurrence for (YYYY-MM-DD)")
    reason: Optional[str] = Field(None, max_length=255, description="Optional skip reason")


class RecurringTaskResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    priority: TaskPriority
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryResponse] = None
    project_id: Optional[uuid.UUID] = None

    frequency: RecurrenceFrequency
    interval: int
    start_date: date
    end_date: Optional[date] = None
    max_occurrences: Optional[int] = None

    weekdays: Optional[List[int]] = None
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    timezone: Optional[str] = None

    next_occurrence_date: Optional[date] = None
    occurrences_generated: int
    is_active: bool
    is_stopped: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecurringTaskListResponse(BaseModel):
    items: List[RecurringTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TriggerGenerationRequest(BaseModel):
    target_date: Optional[date] = Field(None, description="Generate up to target date (max 30 days into future)")


