import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Focus Session Schemas ---

class FocusSessionBase(BaseModel):
    session_type: str = Field(default="FOCUS", pattern="^(FOCUS|SHORT_BREAK|LONG_BREAK)$")
    task_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class FocusSessionStart(FocusSessionBase):
    custom_duration_minutes: Optional[int] = Field(None, ge=1, le=180)


class FocusSessionNotesUpdate(BaseModel):
    notes: Optional[str] = None


class FocusSessionResponse(FocusSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str  # ACTIVE, PAUSED, COMPLETED, ABANDONED
    planned_duration_seconds: int
    actual_duration_seconds: int
    accumulated_pause_seconds: int
    started_at: datetime
    paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields for countdown & sync
    remaining_seconds: int = 0
    is_expired: bool = False

    # Optional references
    task_title: Optional[str] = None
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Focus Preference Schemas ---

class FocusPreferenceBase(BaseModel):
    focus_duration_minutes: int = Field(default=25, ge=1, le=180)
    short_break_duration_minutes: int = Field(default=5, ge=1, le=60)
    long_break_duration_minutes: int = Field(default=15, ge=1, le=60)
    long_break_interval: int = Field(default=4, ge=1, le=12)
    auto_start_breaks: bool = False
    auto_start_focus: bool = False
    sound_enabled: bool = True
    browser_notifications_enabled: bool = True
    daily_goal_minutes: int = Field(default=120, ge=1, le=1440)


class FocusPreferenceUpdate(BaseModel):
    focus_duration_minutes: Optional[int] = Field(None, ge=1, le=180)
    short_break_duration_minutes: Optional[int] = Field(None, ge=1, le=60)
    long_break_duration_minutes: Optional[int] = Field(None, ge=1, le=60)
    long_break_interval: Optional[int] = Field(None, ge=1, le=12)
    auto_start_breaks: Optional[bool] = None
    auto_start_focus: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    browser_notifications_enabled: Optional[bool] = None
    daily_goal_minutes: Optional[int] = Field(None, ge=1, le=1440)


class FocusPreferenceResponse(FocusPreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Focus Analytics Schemas ---

class FocusDailySummary(BaseModel):
    today_focus_seconds: int
    today_completed_sessions: int
    daily_goal_minutes: int
    goal_completion_percentage: float
    streak_days: int = 0


class FocusTrendDay(BaseModel):
    date: str  # YYYY-MM-DD
    focus_minutes: int
    completed_sessions: int


class FocusWeeklyTrends(BaseModel):
    total_focus_minutes: int
    total_completed_sessions: int
    average_session_minutes: float
    days: List[FocusTrendDay]


class FocusTaskBreakdownItem(BaseModel):
    task_id: Optional[uuid.UUID]
    task_title: str
    total_focus_minutes: int
    completed_sessions: int


class FocusProjectBreakdownItem(BaseModel):
    project_id: Optional[uuid.UUID]
    project_name: str
    total_focus_minutes: int
    completed_sessions: int


class FocusAnalyticsOverview(BaseModel):
    daily: FocusDailySummary
    weekly: FocusWeeklyTrends
    task_breakdown: List[FocusTaskBreakdownItem]
    project_breakdown: List[FocusProjectBreakdownItem]
