"""
DayFlow backend – Pydantic request / response schemas.

All timestamps in API responses are ISO-8601 strings with UTC offset.
Scheduled date and time values are plain date / time strings (no tz).
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------------------------------- #
# Shared enums (mirrors models.py but as plain string literals for Pydantic)
# --------------------------------------------------------------------------- #

from enum import Enum


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Category(str, Enum):
    work = "work"
    personal = "personal"
    learning = "learning"
    health = "health"
    other = "other"


class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class EventType(str, Enum):
    created = "created"
    updated = "updated"
    completed = "completed"
    reopened = "reopened"
    deleted = "deleted"
    rescheduled = "rescheduled"


# --------------------------------------------------------------------------- #
# Task schemas
# --------------------------------------------------------------------------- #

class TaskBase(BaseModel):
    """Fields shared across create / update / response."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed description")

    scheduled_date: date = Field(..., description="Local calendar date (Asia/Kolkata)")
    start_time: Optional[time] = Field(None, description="Optional start time (local)")
    end_time: Optional[time] = Field(None, description="Optional end time (local)")

    priority: Priority = Field(Priority.medium, description="Task priority")
    category: Category = Field(Category.other, description="Task category")

    @model_validator(mode="after")
    def _validate_time_range(self) -> "TaskBase":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class TaskCreate(TaskBase):
    """Payload for POST /tasks."""
    pass


class TaskUpdate(BaseModel):
    """
    Payload for PUT /tasks/{task_id}.

    All fields are optional so callers can do partial updates without
    explicitly passing every field.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    priority: Optional[Priority] = None
    category: Optional[Category] = None
    status: Optional[TaskStatus] = None

    @model_validator(mode="after")
    def _validate_time_range(self) -> "TaskUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class TaskReschedule(BaseModel):
    """Payload for PATCH /tasks/{task_id}/reschedule."""
    scheduled_date: date = Field(..., description="New local scheduled date")
    start_time: Optional[time] = Field(None, description="New optional start time")
    end_time: Optional[time] = Field(None, description="New optional end time")

    @model_validator(mode="after")
    def _validate_time_range(self) -> "TaskReschedule":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class TaskResponse(TaskBase):
    """Full task representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    original_scheduled_date: Optional[date] = None


# --------------------------------------------------------------------------- #
# Generic response wrappers
# --------------------------------------------------------------------------- #

class HealthResponse(BaseModel):
    status: str
    version: str


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    task_id: Optional[int] = None


# --------------------------------------------------------------------------- #
# TaskEvent schema
# --------------------------------------------------------------------------- #

class TaskEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    event_type: str
    event_timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def parse_details(cls, data: Any) -> Any:
        # If details is stored as a JSON string in DB model, decode it
        if hasattr(data, "details"):
            raw_details = getattr(data, "details")
            if isinstance(raw_details, str):
                import json
                try:
                    setattr(data, "details", json.loads(raw_details))
                except Exception:
                    pass
        elif isinstance(data, dict) and isinstance(data.get("details"), str):
            import json
            try:
                data["details"] = json.loads(data["details"])
            except Exception:
                pass
        return data


# --------------------------------------------------------------------------- #
# Analytics schemas (Stage 4)
# --------------------------------------------------------------------------- #

class AnalyticsSummary(BaseModel):
    total: int
    completed: int
    pending: int
    overdue: int
    completion_percentage: float


class DailyMetric(BaseModel):
    date: str
    day_name: str
    total: int
    completed: int
    pending: int
    completion_percentage: float


class HeatmapDay(BaseModel):
    date: str
    completed_count: int
    total_scheduled: int
    intensity: int


class CategoryMetric(BaseModel):
    category: str
    total: int
    completed: int
    pending: int


class PriorityMetric(BaseModel):
    priority: str
    total: int
    completed: int
    pending: int


class AnalyticsResponse(BaseModel):
    timezone: str
    reported_at: str
    today_date: str
    summary: AnalyticsSummary
    today: DailyMetric
    seven_day_trend: list[DailyMetric]
    heatmap: list[HeatmapDay]
    category_breakdown: list[CategoryMetric]
    priority_breakdown: list[PriorityMetric]

