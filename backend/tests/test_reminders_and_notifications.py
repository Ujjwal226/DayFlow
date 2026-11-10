import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.reminder import Reminder, Notification, NotificationPreference, EmailDelivery
from app.models.task import Task
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.services.scheduler_service import ReminderSchedulerService
from app.services.email_service import SMTPEmailProvider


@pytest.fixture
def user_a(db_session: Session):
    user = User(
        email="rem_user_a@example.com",
        display_name="Reminder User A",
        hashed_password=hash_password("PasswordA123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session: Session):
    user = User(
        email="rem_user_b@example.com",
        display_name="Reminder User B",
        hashed_password=hash_password("PasswordB123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_a(user_a: User):
    token = create_access_token(user_id=user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(user_b: User):
    token = create_access_token(user_id=user_b.id)
    return {"Authorization": f"Bearer {token}"}


def test_reminder_crud_and_tenant_isolation(client: TestClient, db_session: Session, auth_headers_a, auth_headers_b):
    # 1. Create reminder for User A
    sched = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    resp = client.post(
        "/api/v1/reminders",
        headers=auth_headers_a,
        json={
            "title": "Review financial statements",
            "description": "Quarterly statements check",
            "scheduled_at": sched,
            "timezone": "UTC",
            "recurrence": "DAILY",
            "delivery_channels": "IN_APP,EMAIL",
        },
    )
    assert resp.status_code == 201
    reminder_id = resp.json()["id"]
    assert resp.json()["title"] == "Review financial statements"
    assert resp.json()["status"] == "PENDING"
    assert resp.json()["recurrence"] == "DAILY"

    # 2. User B cannot access or see User A's reminder
    resp_ub = client.get(f"/api/v1/reminders/{reminder_id}", headers=auth_headers_b)
    assert resp_ub.status_code == 404

    resp_list_ub = client.get("/api/v1/reminders", headers=auth_headers_b)
    assert resp_list_ub.status_code == 200
    assert not any(r["id"] == reminder_id for r in resp_list_ub.json())

    # 3. User A can get and update reminder
    patch_resp = client.patch(
        f"/api/v1/reminders/{reminder_id}",
        headers=auth_headers_a,
        json={"title": "Updated Review Title"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Review Title"

    # 4. Snooze reminder
    snooze_resp = client.post(
        f"/api/v1/reminders/{reminder_id}/snooze",
        headers=auth_headers_a,
        json={"snooze_minutes": 15},
    )
    assert snooze_resp.status_code == 200
    assert snooze_resp.json()["status"] == "SNOOZED"
    assert snooze_resp.json()["snoozed_until"] is not None

    # 5. Complete reminder
    comp_resp = client.post(f"/api/v1/reminders/{reminder_id}/complete", headers=auth_headers_a)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "COMPLETED"

    # 6. Delete reminder
    del_resp = client.delete(f"/api/v1/reminders/{reminder_id}", headers=auth_headers_a)
    assert del_resp.status_code == 204

    # Verify 404 after deletion
    get_after = client.get(f"/api/v1/reminders/{reminder_id}", headers=auth_headers_a)
    assert get_after.status_code == 404


def test_reminder_with_task_association(client: TestClient, db_session: Session, user_a: User, auth_headers_a, auth_headers_b):
    # 1. Create a task for User A
    task = Task(
        user_id=user_a.id,
        title="Prepare tax documents",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # 2. Create reminder linking User A's task
    sched = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    rem_resp = client.post(
        "/api/v1/reminders",
        headers=auth_headers_a,
        json={
            "title": "Tax reminder",
            "scheduled_at": sched,
            "task_id": str(task.id),
        },
    )
    assert rem_resp.status_code == 201
    assert rem_resp.json()["task_id"] == str(task.id)

    # 3. User B cannot link User A's task to their reminder
    rem2_resp = client.post(
        "/api/v1/reminders",
        headers=auth_headers_b,
        json={
            "title": "Malicious task link",
            "scheduled_at": sched,
            "task_id": str(task.id),
        },
    )
    assert rem2_resp.status_code == 404


def test_notifications_workflow_and_preferences(client: TestClient, db_session: Session, auth_headers_a):
    # Check initial unread count
    cnt_resp = client.get("/api/v1/notifications/unread-count", headers=auth_headers_a)
    assert cnt_resp.status_code == 200
    assert cnt_resp.json()["unread_count"] == 0

    # Check notification preferences endpoint
    pref_resp = client.get("/api/v1/notification-preferences", headers=auth_headers_a)
    assert pref_resp.status_code == 200
    assert pref_resp.json()["in_app_enabled"] is True
    assert pref_resp.json()["email_enabled"] is True

    # Update preferences
    pref_patch = client.patch(
        "/api/v1/notification-preferences",
        headers=auth_headers_a,
        json={"quiet_hours_enabled": True, "quiet_hours_start": "22:00", "quiet_hours_end": "08:00"},
    )
    assert pref_patch.status_code == 200
    assert pref_patch.json()["quiet_hours_enabled"] is True
    assert pref_patch.json()["quiet_hours_start"] == "22:00"


def test_scheduler_due_processing_and_recurring(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # Create a due recurring reminder directly
    now = datetime.now(timezone.utc)
    due_time = now - timedelta(minutes=5)
    resp = client.post(
        "/api/v1/reminders",
        headers=auth_headers_a,
        json={
            "title": "Daily Standup Meeting",
            "scheduled_at": due_time.isoformat(),
            "recurrence": "DAILY",
            "delivery_channels": "IN_APP,EMAIL",
        },
    )
    assert resp.status_code == 201

    # Run scheduler service using the fixture session
    scheduler = ReminderSchedulerService(db_session)
    processed = scheduler.process_due_reminders(now)
    assert processed >= 1

    # Verify notification created
    notifs = client.get("/api/v1/notifications", headers=auth_headers_a).json()
    assert any("Daily Standup Meeting" in n["title"] for n in notifs)

    # Check unread count increased
    unread = client.get("/api/v1/notifications/unread-count", headers=auth_headers_a).json()
    assert unread["unread_count"] >= 1

    # Mark all read
    mark_resp = client.post("/api/v1/notifications/mark-all-read", headers=auth_headers_a)
    assert mark_resp.status_code == 200

    unread_after = client.get("/api/v1/notifications/unread-count", headers=auth_headers_a).json()
    assert unread_after["unread_count"] == 0

    # Test pending email processing
    emails_sent = scheduler.process_pending_emails(now)
    assert emails_sent >= 1


# --- Focused Reliability & Idempotency Tests ---

def test_idempotency_and_no_duplicate_processing_after_advancement(db_session: Session, user_a: User):
    """Ensure a processed due reminder is advanced and second run does not duplicate notifications."""
    now = datetime.now(timezone.utc)
    sched_time = now - timedelta(minutes=10)

    reminder = Reminder(
        user_id=user_a.id,
        title="Weekly Sync",
        scheduled_at=sched_time,
        timezone="America/New_York",
        recurrence="WEEKLY",
        delivery_channels="IN_APP",
        status="PENDING",
    )
    db_session.add(reminder)
    db_session.commit()

    scheduler = ReminderSchedulerService(db_session)

    # Run 1: processes the reminder and advances it by 1 week
    first_run_processed = scheduler.process_due_reminders(now)
    assert first_run_processed == 1

    notifs_run_1 = db_session.query(Notification).filter(Notification.user_id == user_a.id).all()
    assert len(notifs_run_1) == 1

    # Run 2: immediately afterwards, must process 0 items because scheduled_at is now 1 week in the future
    second_run_processed = scheduler.process_due_reminders(now)
    assert second_run_processed == 0

    notifs_run_2 = db_session.query(Notification).filter(Notification.user_id == user_a.id).all()
    assert len(notifs_run_2) == 1


def test_timezone_recurrence_monthly_clamping(db_session: Session, user_a: User):
    """Ensure monthly recurrence calculation handles month end boundary correctly (e.g. Jan 31 -> Feb 28)."""
    scheduler = ReminderSchedulerService(db_session)
    jan_31 = datetime(2026, 1, 31, 14, 0, tzinfo=timezone.utc)

    reminder = Reminder(
        user_id=user_a.id,
        title="Month-End Closing",
        scheduled_at=jan_31,
        timezone="UTC",
        recurrence="MONTHLY",
        delivery_channels="IN_APP",
        status="PENDING",
    )

    next_time = scheduler.advance_recurrence(reminder)
    assert next_time is not None
    # February 2026 has 28 days
    assert next_time.year == 2026
    assert next_time.month == 2
    assert next_time.day == 28
    assert next_time.hour == 14


def test_quiet_hours_suppresses_email_delivery_queueing(db_session: Session, user_a: User):
    """Ensure that when quiet hours are active, email outbox entry is suppressed."""
    pref = NotificationPreference(
        user_id=user_a.id,
        in_app_enabled=True,
        email_enabled=True,
        quiet_hours_enabled=True,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        preferred_timezone="UTC",
    )
    db_session.add(pref)
    db_session.commit()

    now_quiet = datetime(2026, 11, 11, 23, 30, tzinfo=timezone.utc)
    due_time = now_quiet - timedelta(minutes=5)

    reminder = Reminder(
        user_id=user_a.id,
        title="Late night alert",
        scheduled_at=due_time,
        timezone="UTC",
        recurrence="NONE",
        delivery_channels="IN_APP,EMAIL",
        status="PENDING",
    )
    db_session.add(reminder)
    db_session.commit()

    scheduler = ReminderSchedulerService(db_session)
    scheduler.process_due_reminders(now_quiet)

    # In-app notification created
    notifs = db_session.query(Notification).filter(Notification.user_id == user_a.id, Notification.title.like("%Late night%")).all()
    assert len(notifs) == 1

    # Email delivery outbox entry must be suppressed during quiet hours
    emails = db_session.query(EmailDelivery).filter(EmailDelivery.user_id == user_a.id, EmailDelivery.subject.like("%Late night%")).all()
    assert len(emails) == 0


def test_email_outbox_exponential_backoff_and_terminal_failure(db_session: Session, user_a: User, monkeypatch):
    """Verify that email delivery retries use bounded exponential backoff and reach FAILED after 5 attempts."""
    now = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)
    delivery = EmailDelivery(
        user_id=user_a.id,
        recipient_email=user_a.email,
        subject="Retry Test",
        body="Body",
        status="PENDING",
        attempts=0,
        next_retry_at=now,
    )
    db_session.add(delivery)
    db_session.commit()

    scheduler = ReminderSchedulerService(db_session)

    # Mock email provider to fail with simulated network error
    def failing_send(*args, **kwargs):
        raise ConnectionRefusedError("SMTP connection refused")

    monkeypatch.setattr(scheduler.email_provider, "send_reminder_email", failing_send)

    # Attempt 1: backoff should be 30 * 2^0 = 30 seconds
    scheduler.process_pending_emails(now)
    db_session.refresh(delivery)
    assert delivery.attempts == 1
    assert delivery.status == "PENDING"
    assert delivery.next_retry_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=30)
    assert "SMTP connection refused" in delivery.error_message

    # Attempt 2, 3, 4: simulate reaching 4 attempts
    delivery.attempts = 4
    delivery.next_retry_at = now
    db_session.commit()

    # Attempt 5: terminal failure
    scheduler.process_pending_emails(now)
    db_session.refresh(delivery)
    assert delivery.attempts == 5
    assert delivery.status == "FAILED"
    assert delivery.next_retry_at is None


def test_smtp_error_sanitization():
    """Verify SMTP exception sanitization prevents password exposure."""
    from app.core.config import settings
    orig_pwd = settings.SMTP_PASSWORD
    try:
        settings.SMTP_PASSWORD = "SuperSecretPassword123"
        settings.SMTP_HOST = "localhost"
        settings.EMAIL_FROM = "test@example.com"
        provider = SMTPEmailProvider()

        # Simulate exception containing the secret password
        with pytest.raises(RuntimeError) as exc_info:
            # Triggering send to invalid port/host will fail
            provider._send_message("recipient@example.com", "Test", "Body")
        
        # Ensure password is not in the raised message
        assert "SuperSecretPassword123" not in str(exc_info.value)
    finally:
        settings.SMTP_PASSWORD = orig_pwd


def test_smtp_crash_window_and_worker_recovery_at_least_once(db_session: Session, user_a: User, monkeypatch):
    """Verify SMTP crash window semantics:
    
    If SMTP accepts the message but worker crashes before committing SENT status to DB,
    a restarted worker safely picks up the delivery and re-transmits with the same
    deterministic Message-ID for downstream MTA deduplication.
    """
    now = datetime(2026, 11, 11, 11, 0, tzinfo=timezone.utc)
    delivery = EmailDelivery(
        user_id=user_a.id,
        recipient_email=user_a.email,
        subject="Crash Window Test",
        body="Body content",
        status="PENDING",
        attempts=0,
        next_retry_at=now,
    )
    db_session.add(delivery)
    db_session.commit()

    captured_message_ids = []

    def mock_send_reminder(to_email, display_name, title, description=None, task_title=None, scheduled_at_str=None, message_id=None):
        captured_message_ids.append(message_id)

    scheduler_worker_1 = ReminderSchedulerService(db_session)
    monkeypatch.setattr(scheduler_worker_1.email_provider, "send_reminder_email", mock_send_reminder)

    delivery_id = delivery.id

    # Worker 1 sends the email but simulates a process crash/failure before committing SENT
    mock_send_reminder(
        to_email=delivery.recipient_email,
        display_name="User",
        title=delivery.subject,
        message_id=f"<{delivery_id}@dayflow.app>",
    )
    # The delivery in DB remained PENDING (e.g. crash before update_email_delivery/commit)
    assert len(captured_message_ids) == 1

    # Worker 2 restarts and processes pending deliveries
    scheduler_worker_2 = ReminderSchedulerService(db_session)
    monkeypatch.setattr(scheduler_worker_2.email_provider, "send_reminder_email", mock_send_reminder)

    sent_count = scheduler_worker_2.process_pending_emails(now)
    assert sent_count == 1

    reloaded = db_session.query(EmailDelivery).filter(EmailDelivery.id == delivery_id).first()
    assert reloaded is not None
    assert reloaded.status == "SENT"
    assert len(captured_message_ids) == 2

    # Verify both transmissions used the identical deterministic Message-ID
    assert captured_message_ids[0] == captured_message_ids[1]
    assert captured_message_ids[0] == f"<{delivery_id}@dayflow.app>"


def test_concurrent_worker_claiming_skip_locked(db_session: Session, user_a: User):
    """Test that lock=True query handles locking safely on the active database engine."""
    now = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
    delivery = EmailDelivery(
        user_id=user_a.id,
        recipient_email=user_a.email,
        subject="Concurrent Claim Test",
        body="Body",
        status="PENDING",
        attempts=0,
        next_retry_at=now,
    )
    db_session.add(delivery)
    db_session.commit()

    repo = NotificationRepository(db_session)
    # SQLite in tests will skip FOR UPDATE SKIP LOCKED gracefully, while PostgreSQL dialect applies it
    deliveries = repo.get_pending_email_deliveries(now, lock=True)
    assert len(deliveries) >= 1
    assert deliveries[0].id == delivery.id
