import uuid
from datetime import date, datetime
from typing import List, Optional
import zoneinfo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def validate_iana_timezone(v: Optional[str]) -> str:
    tz_str = v.strip() if v else "UTC"
    try:
        zoneinfo.ZoneInfo(tz_str)
    except Exception:
        raise ValueError(f"Invalid IANA timezone identifier: '{tz_str}'")
    return tz_str


class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the calendar event")
    description: Optional[str] = Field(None, max_length=5000, description="Detailed description")
    location: Optional[str] = Field(None, max_length=255, description="Event location or link")
    color: Optional[str] = Field(None, max_length=50, description="Hex color or CSS tag")
    is_all_day: bool = Field(False, description="Whether event is all-day")
    timezone: str = Field("UTC", max_length=50, description="IANA timezone identifier")
    task_id: Optional[uuid.UUID] = Field(None, description="Optional associated task ID")

    # Timed event fields
    start_at: Optional[datetime] = Field(None, description="UTC start datetime for timed events")
    end_at: Optional[datetime] = Field(None, description="UTC end datetime for timed events")

    # All-day event fields
    start_date: Optional[date] = Field(None, description="Start date for all-day events")
    end_date: Optional[date] = Field(None, description="Exclusive end date for all-day events")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or contain only whitespace.")
        return trimmed

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, v: str) -> str:
        return validate_iana_timezone(v)


class CalendarEventCreate(CalendarEventBase):
    @model_validator(mode="after")
    def validate_representation(self) -> "CalendarEventCreate":
        if not self.is_all_day:
            if self.start_at is None or self.end_at is None:
                raise ValueError("Timed events (is_all_day=False) require both 'start_at' and 'end_at'.")
            if self.start_date is not None or self.end_date is not None:
                raise ValueError("Timed events (is_all_day=False) must not include 'start_date' or 'end_date'.")
            if self.end_at <= self.start_at:
                raise ValueError("Timed event 'end_at' must be strictly after 'start_at'.")
        else:
            if self.start_date is None or self.end_date is None:
                raise ValueError("All-day events (is_all_day=True) require both 'start_date' and 'end_date'.")
            if self.start_at is not None or self.end_at is not None:
                raise ValueError("All-day events (is_all_day=True) must not include 'start_at' or 'end_at'.")
            if self.end_date <= self.start_date:
                raise ValueError("All-day event 'end_date' must be strictly after 'start_date'.")
        return self


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    location: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=50)
    is_all_day: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    task_id: Optional[uuid.UUID] = None

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Title cannot be empty or contain only whitespace.")
            return trimmed
        return v

    @field_validator("timezone")
    @classmethod
    def check_tz_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_iana_timezone(v)
        return v


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
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
    created_at: datetime
    updated_at: datetime


class CalendarEventListResponse(BaseModel):
    items: List[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

