import logging
import uuid
import calendar
from datetime import datetime, timedelta, timezone, time
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.reminder import Reminder, Notification, EmailDelivery, NotificationPreference
from app.models.user import User
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import get_email_provider

logger = logging.getLogger("dayflow.scheduler")

MAX_EMAIL_ATTEMPTS = 5
BACKOFF_BASE_SECONDS = 30


class ReminderSchedulerService:
    """Service to process due reminders and retry failed email deliveries."""

    def __init__(self, db: Session):
        self.db = db
        self.reminder_repo = ReminderRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.email_provider = get_email_provider()

    @staticmethod
    def _add_month(dt: datetime) -> datetime:
        """Accurately adds one calendar month preserving time and clamping to month end."""
        year = dt.year + (dt.month // 12)
        month = (dt.month % 12) + 1
        _, max_day = calendar.monthrange(year, month)
        day = min(dt.day, max_day)
        return dt.replace(year=year, month=month, day=day)

    def advance_recurrence(self, reminder: Reminder) -> Optional[datetime]:
        """Calculates next recurrence time for recurring reminder respecting timezone and month boundaries."""
        tz_name = reminder.timezone or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc

        # Convert UTC scheduled_at to local timezone
        local_sched = reminder.scheduled_at.astimezone(tz)

        if reminder.recurrence == "DAILY":
            next_local = local_sched + timedelta(days=1)
        elif reminder.recurrence == "WEEKLY":
            next_local = local_sched + timedelta(weeks=1)
        elif reminder.recurrence == "MONTHLY":
            next_local = self._add_month(local_sched)
        else:
            return None

        # Return converted back to UTC
        return next_local.astimezone(timezone.utc)

    @staticmethod
    def is_in_quiet_hours(pref: Optional[NotificationPreference], current_time: datetime) -> bool:
        """Determines if the current moment falls in the user's quiet hours."""
        if not pref or not pref.quiet_hours_enabled:
            return False
        if not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False

        try:
            tz = ZoneInfo(pref.preferred_timezone or "UTC")
        except Exception:
            tz = timezone.utc

        local_now = current_time.astimezone(tz).time()
        start_parts = [int(p) for p in pref.quiet_hours_start.split(":")]
        end_parts = [int(p) for p in pref.quiet_hours_end.split(":")]
        start_time = time(start_parts[0], start_parts[1])
        end_time = time(end_parts[0], end_parts[1])

        if start_time < end_time:
            return start_time <= local_now < end_time
        else:
            # Overnights quiet hours (e.g. 22:00 to 08:00)
            return local_now >= start_time or local_now < end_time

    def process_due_reminders(self, current_time: Optional[datetime] = None) -> int:
        """Processes all pending or snoozed reminders that are due using atomic claiming."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        due_reminders = self.reminder_repo.get_due_reminders(current_time, lock=True)
        processed_count = 0

        for reminder in due_reminders:
            try:
                # 1. Fetch user preferences
                pref = self.notification_repo.get_preference(reminder.user_id)
                user = self.db.query(User).filter(User.id == reminder.user_id).first()
                if not user:
                    continue

                in_app_enabled = pref.in_app_enabled if pref else True
                email_enabled = pref.email_enabled if pref else True
                channels = [c.strip().upper() for c in reminder.delivery_channels.split(",")]

                in_quiet = self.is_in_quiet_hours(pref, current_time)

                # 2. Create in-app notification if channel specified and pref enabled
                notification = None
                if "IN_APP" in channels and in_app_enabled:
                    notification = Notification(
                        user_id=reminder.user_id,
                        reminder_id=reminder.id,
                        task_id=reminder.task_id,
                        title=f"Reminder: {reminder.title}",
                        message=reminder.description or f"Reminder scheduled for {reminder.scheduled_at.isoformat()}",
                        type="REMINDER",
                    )
                    self.notification_repo.create(notification)

                # 3. Create email delivery outbox entry if email channel specified, pref enabled, and not quiet hours
                if "EMAIL" in channels and email_enabled and not in_quiet:
                    task_title = reminder.task.title if reminder.task else None
                    email_delivery = EmailDelivery(
                        user_id=reminder.user_id,
                        notification_id=notification.id if notification else None,
                        recipient_email=user.email,
                        subject=f"DayFlow Reminder: {reminder.title}",
                        body=reminder.description or f"Reminder: {reminder.title}",
                        status="PENDING",
                        attempts=0,
                        next_retry_at=current_time,
                    )
                    self.notification_repo.create_email_delivery(email_delivery)

                # 4. Advance recurrence or set status
                next_time = self.advance_recurrence(reminder)
                if next_time:
                    reminder.scheduled_at = next_time
                    reminder.status = "PENDING"
                    reminder.snoozed_until = None
                else:
                    reminder.status = "SENT"
                    reminder.snoozed_until = None

                self.reminder_repo.update(reminder)
                self.db.commit()
                processed_count += 1
            except Exception as e:
                self.db.rollback()
                logger.error("Error processing due reminder %s: %s", reminder.id, str(e))

        return processed_count

    def process_pending_emails(self, current_time: Optional[datetime] = None) -> int:
        """Dispatches pending emails with exponential backoff, atomic locking, and error isolation."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        deliveries = self.notification_repo.get_pending_email_deliveries(current_time, lock=True)
        sent_count = 0

        for delivery in deliveries:
            delivery_id = delivery.id
            attempts = delivery.attempts + 1
            user = self.db.query(User).filter(User.id == delivery.user_id).first()
            display_name = user.display_name if user else "DayFlow User"
            deterministic_message_id = f"<{delivery_id}@dayflow.app>"

            delivery.attempts = attempts
            delivery.last_attempt_at = current_time

            try:
                self.email_provider.send_reminder_email(
                    to_email=delivery.recipient_email,
                    display_name=display_name,
                    title=delivery.subject,
                    description=delivery.body,
                    message_id=deterministic_message_id,
                )
                delivery.status = "SENT"
                delivery.error_message = None
                delivery.next_retry_at = None
                self.notification_repo.update_email_delivery(delivery)
                self.db.commit()
                sent_count += 1
            except Exception as exc:
                sanitized_error = str(exc)
                logger.warning(
                    "Failed to deliver email %s (attempt %d/%d): %s",
                    delivery_id,
                    attempts,
                    MAX_EMAIL_ATTEMPTS,
                    sanitized_error,
                )
                delivery.error_message = sanitized_error[:500]
                if attempts >= MAX_EMAIL_ATTEMPTS:
                    delivery.status = "FAILED"
                    delivery.next_retry_at = None
                else:
                    # Exponential backoff: base * 2^(attempts-1)
                    backoff = BACKOFF_BASE_SECONDS * (2 ** (attempts - 1))
                    delivery.next_retry_at = current_time + timedelta(seconds=backoff)
                self.notification_repo.update_email_delivery(delivery)
                self.db.commit()

        return sent_count
