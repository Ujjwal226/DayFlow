import logging
import uuid
import calendar
from datetime import datetime, timedelta, timezone, time
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.reminder import Reminder, Notification, EmailDelivery, NotificationPreference
from app.models.user import User
from app.models.goal import Goal, GoalMilestone, PlanningObjective, GoalStatus, ProgressCalculationMethod
from app.models.finance import Budget
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import get_email_provider
from app.services.finance_service import FinanceService

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

    def process_goal_notifications(self, current_time: Optional[datetime] = None) -> int:
        """
        Processes goal-related notifications:
        - Upcoming goal deadlines (within 48h)
        - Overdue goals
        - Upcoming milestone deadlines (within 24h)
        - Daily planning reminders
        Deduplicates against existing notifications and respects user notification preferences & quiet hours.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        processed_count = 0
        today_date = current_time.date()

        # 1. Active goals
        active_goals = (
            self.db.query(Goal)
            .filter(
                Goal.is_archived.is_(False),
                Goal.status.notin_([GoalStatus.COMPLETED.value, GoalStatus.CANCELLED.value]),
                Goal.target_date.isnot(None),
            )
            .all()
        )

        for goal in active_goals:
            try:
                pref = self.notification_repo.get_preference(goal.user_id)
                user = self.db.query(User).filter(User.id == goal.user_id).first()
                if not user:
                    continue

                in_app_enabled = pref.in_app_enabled if pref else True
                email_enabled = pref.email_enabled if pref else True
                due_date_enabled = pref.due_date_reminders_enabled if pref else True
                overdue_enabled = pref.overdue_reminders_enabled if pref else True
                in_quiet = self.is_in_quiet_hours(pref, current_time)

                days_to_target = (goal.target_date - today_date).days

                # A. Overdue Goal Notification
                if days_to_target < 0 and overdue_enabled:
                    notif_type = "GOAL_OVERDUE"
                    title = f"Goal Overdue: {goal.title}"
                    # Check deduplication: notification for this specific goal_id, type & date
                    # Stored in message or checked by unique title matching the goal title & ID
                    existing = (
                        self.db.query(Notification)
                        .filter(
                            Notification.user_id == goal.user_id,
                            Notification.type == notif_type,
                            Notification.title == title,
                            Notification.message.like(f"%[{goal.id}]%"),
                            Notification.created_at >= datetime.combine(today_date, time.min, tzinfo=timezone.utc),
                        )
                        .first()
                    )
                    if not existing:
                        notification = None
                        if in_app_enabled:
                            notification = Notification(
                                user_id=goal.user_id,
                                title=title,
                                message=f"Goal '{goal.title}' [{goal.id}] was due on {goal.target_date.isoformat()} and is currently at {goal.progress_percentage}% progress.",
                                type=notif_type,
                            )
                            self.notification_repo.create(notification)

                        if email_enabled and not in_quiet:
                            email_delivery = EmailDelivery(
                                user_id=goal.user_id,
                                notification_id=notification.id if notification else None,
                                recipient_email=user.email,
                                subject=f"DayFlow Alert: {title}",
                                body=f"Your goal '{goal.title}' [{goal.id}] is overdue (due {goal.target_date.isoformat()}). Current progress: {goal.progress_percentage}%.",
                                status="PENDING",
                                attempts=0,
                                next_retry_at=current_time,
                            )
                            self.notification_repo.create_email_delivery(email_delivery)

                        self.db.commit()
                        processed_count += 1

                # B. Approaching Goal Deadline Notification (within 2 days / 48 hours)
                elif 0 <= days_to_target <= 2 and due_date_enabled:
                    notif_type = "GOAL_DEADLINE"
                    day_str = "today" if days_to_target == 0 else f"in {days_to_target} day{'s' if days_to_target > 1 else ''}"
                    title = f"Goal Deadline Approaching: {goal.title}"
                    existing = (
                        self.db.query(Notification)
                        .filter(
                            Notification.user_id == goal.user_id,
                            Notification.type == notif_type,
                            Notification.title == title,
                            Notification.message.like(f"%[{goal.id}]%"),
                            Notification.created_at >= datetime.combine(today_date, time.min, tzinfo=timezone.utc),
                        )
                        .first()
                    )
                    if not existing:
                        notification = None
                        if in_app_enabled:
                            notification = Notification(
                                user_id=goal.user_id,
                                title=title,
                                message=f"Goal '{goal.title}' [{goal.id}] is due {day_str} ({goal.target_date.isoformat()}). Current progress: {goal.progress_percentage}%.",
                                type=notif_type,
                            )
                            self.notification_repo.create(notification)

                        if email_enabled and not in_quiet:
                            email_delivery = EmailDelivery(
                                user_id=goal.user_id,
                                notification_id=notification.id if notification else None,
                                recipient_email=user.email,
                                subject=f"DayFlow Reminder: {title}",
                                body=f"Your goal '{goal.title}' [{goal.id}] is due {day_str} ({goal.target_date.isoformat()}). Progress is currently at {goal.progress_percentage}%.",
                                status="PENDING",
                                attempts=0,
                                next_retry_at=current_time,
                            )
                            self.notification_repo.create_email_delivery(email_delivery)

                        self.db.commit()
                        processed_count += 1

            except Exception as e:
                self.db.rollback()
                logger.error("Error processing goal notification for goal %s: %s", goal.id, str(e), exc_info=True)

        # 2. Approaching Milestone Deadlines (due within 1 day)
        active_milestones = (
            self.db.query(GoalMilestone)
            .join(Goal, GoalMilestone.goal_id == Goal.id)
            .filter(
                Goal.is_archived.is_(False),
                Goal.status.notin_([GoalStatus.COMPLETED.value, GoalStatus.CANCELLED.value]),
                GoalMilestone.is_completed.is_(False),
                GoalMilestone.due_date.isnot(None),
            )
            .all()
        )

        for ms in active_milestones:
            try:
                days_to_ms = (ms.due_date - today_date).days
                if 0 <= days_to_ms <= 1:
                    pref = self.notification_repo.get_preference(ms.goal.user_id)
                    user = self.db.query(User).filter(User.id == ms.goal.user_id).first()
                    if not user:
                        continue

                    in_app_enabled = pref.in_app_enabled if pref else True
                    email_enabled = pref.email_enabled if pref else True
                    due_date_enabled = pref.due_date_reminders_enabled if pref else True
                    in_quiet = self.is_in_quiet_hours(pref, current_time)

                    if due_date_enabled:
                        notif_type = "MILESTONE_DUE"
                        title = f"Milestone Due Soon: {ms.title}"
                        existing = (
                            self.db.query(Notification)
                            .filter(
                                Notification.user_id == ms.goal.user_id,
                                Notification.type == notif_type,
                                Notification.title == title,
                                Notification.message.like(f"%[{ms.id}]%"),
                                Notification.created_at >= datetime.combine(today_date, time.min, tzinfo=timezone.utc),
                            )
                            .first()
                        )
                        if not existing:
                            notification = None
                            if in_app_enabled:
                                notification = Notification(
                                    user_id=ms.goal.user_id,
                                    title=title,
                                    message=f"Milestone '{ms.title}' [{ms.id}] for goal '{ms.goal.title}' is due on {ms.due_date.isoformat()}.",
                                    type=notif_type,
                                )
                                self.notification_repo.create(notification)

                            if email_enabled and not in_quiet:
                                email_delivery = EmailDelivery(
                                    user_id=ms.goal.user_id,
                                    notification_id=notification.id if notification else None,
                                    recipient_email=user.email,
                                    subject=f"DayFlow Milestone Alert: {title}",
                                    body=f"Milestone '{ms.title}' [{ms.id}] for goal '{ms.goal.title}' is due on {ms.due_date.isoformat()}.",
                                    status="PENDING",
                                    attempts=0,
                                    next_retry_at=current_time,
                                )
                                self.notification_repo.create_email_delivery(email_delivery)

                            self.db.commit()
                            processed_count += 1
            except Exception as e:
                self.db.rollback()
                logger.error("Error processing milestone notification %s: %s", ms.id, str(e))

        return processed_count
    def process_recurring_financial_transactions(self) -> int:
        """Processes due recurring financial transactions idempotently."""
        try:
            finance_service = FinanceService(self.db)
            return finance_service.process_due_recurring_transactions()
        except Exception as e:
            self.db.rollback()
            logger.error("Error processing recurring financial transactions: %s", str(e))
            return 0

    def process_budget_notifications(self, current_time: Optional[datetime] = None) -> int:
        """Checks monthly budgets against 75%, 90%, 100% thresholds and creates alerts respecting quiet hours & user preferences."""
        now_utc = current_time or datetime.now(timezone.utc)
        today = now_utc.date()
        year = today.year
        month = today.month

        budgets = self.db.query(Budget).filter(Budget.year == year, Budget.month == month).all()
        processed_count = 0
        finance_service = FinanceService(self.db)

        for budget in budgets:
            try:
                spent = finance_service.repo.calculate_budget_spent(budget)
                if budget.amount <= 0:
                    continue

                pct = (spent / budget.amount) * 100

                # Check thresholds
                threshold_to_alert = None
                if pct >= 100 and not budget.alert_100_sent:
                    threshold_to_alert = 100
                elif pct >= 90 and not budget.alert_90_sent:
                    threshold_to_alert = 90
                elif pct >= 75 and not budget.alert_75_sent:
                    threshold_to_alert = 75

                if threshold_to_alert:
                    user = self.db.query(User).filter(User.id == budget.user_id).first()
                    if not user:
                        continue

                    pref = self.notification_repo.get_preference(user.id)
                    in_quiet = self.is_in_quiet_hours(pref, now_utc)

                    cat_name = budget.category.name if budget.category else "Overall"
                    title = f"Budget Alert: {threshold_to_alert}% reached for {cat_name}"
                    message = f"You have spent {budget.currency} {spent} of your {budget.currency} {budget.amount} budget for {cat_name} ({pct:.1f}%)."

                    in_app_enabled = pref.in_app_enabled if pref else True
                    email_enabled = pref.email_enabled if pref else True

                    notification = None
                    if in_app_enabled:
                        notification = Notification(
                            user_id=user.id,
                            title=title,
                            message=message,
                            type="SYSTEM_ALERT",
                        )
                        self.notification_repo.create(notification)

                    if email_enabled and not in_quiet:
                        email_delivery = EmailDelivery(
                            user_id=user.id,
                            notification_id=notification.id if notification else None,
                            recipient_email=user.email,
                            subject=f"DayFlow Finance Alert: {title}",
                            body=message,
                            status="PENDING",
                            attempts=0,
                            next_retry_at=now_utc,
                        )
                        self.notification_repo.create_email_delivery(email_delivery)

                    if threshold_to_alert == 100:
                        budget.alert_100_sent = True
                    elif threshold_to_alert == 90:
                        budget.alert_90_sent = True
                    elif threshold_to_alert == 75:
                        budget.alert_75_sent = True

                    self.db.commit()
                    processed_count += 1
            except Exception as e:
                self.db.rollback()
                logger.error("Error processing budget notification for budget %s: %s", budget.id, str(e))

        return processed_count
