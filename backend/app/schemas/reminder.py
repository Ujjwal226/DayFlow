import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Reminder Schemas ---

class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_at: datetime
    timezone: str = "UTC"
    recurrence: str = Field(default="NONE", pattern="^(NONE|DAILY|WEEKLY|MONTHLY)$")
    delivery_channels: str = Field(default="IN_APP", description="Comma-separated: IN_APP, EMAIL, or IN_APP,EMAIL")
    task_id: Optional[uuid.UUID] = None


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    recurrence: Optional[str] = Field(None, pattern="^(NONE|DAILY|WEEKLY|MONTHLY)$")
    delivery_channels: Optional[str] = None
    task_id: Optional[uuid.UUID] = None
    status: Optional[str] = Field(None, pattern="^(PENDING|SENT|COMPLETED|DISMISSED|SNOOZED)$")


class ReminderSnooze(BaseModel):
    snooze_minutes: int = Field(..., ge=1, le=43200)  # Up to 30 days


class ReminderResponse(ReminderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    snoozed_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Notification Schemas ---

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "REMINDER"
    reminder_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int


# --- Notification Preferences Schemas ---

class NotificationPreferenceBase(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = True
    task_reminders_enabled: bool = True
    due_date_reminders_enabled: bool = True
    overdue_reminders_enabled: bool = True
    preferred_timezone: str = "UTC"
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    task_reminders_enabled: Optional[bool] = None
    due_date_reminders_enabled: Optional[bool] = None
    overdue_reminders_enabled: Optional[bool] = None
    preferred_timezone: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Email Delivery Schemas ---

class EmailDeliveryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_id: Optional[uuid.UUID] = None
    recipient_email: str
    subject: str
    status: str
    attempts: int
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

