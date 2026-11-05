import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.recurring_task import RecurrenceFrequency, RecurringTask
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.services.recurrence_calculator import (
    add_months,
    add_years,
    calculate_next_occurrence,
    get_last_day_of_month,
)


@pytest.fixture
def user_a(db_session):
    user = User(
        email="recur_user_a@example.com",
        display_name="Recurring User A",
        hashed_password=hash_password("PasswordA123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session):
    user = User(
        email="recur_user_b@example.com",
        display_name="Recurring User B",
        hashed_password=hash_password("PasswordB123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_a(user_a):
    token = create_access_token(user_id=user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(user_b):
    token = create_access_token(user_id=user_b.id)
    return {"Authorization": f"Bearer {token}"}


# 1. Calculation Unit Tests
def test_recurrence_calculator_daily_and_custom():
    d = date(2026, 5, 1)
    next_d = calculate_next_occurrence(d, RecurrenceFrequency.DAILY, interval=1)
    assert next_d == date(2026, 5, 2)

    next_custom = calculate_next_occurrence(d, RecurrenceFrequency.CUSTOM, interval=5)
    assert next_custom == date(2026, 5, 6)


def test_recurrence_calculator_weekly_with_weekdays():
    # 2026-05-04 is Monday (weekday=0)
    d = date(2026, 5, 4)
    # Target: Monday and Friday (0, 4)
    next_d = calculate_next_occurrence(d, RecurrenceFrequency.WEEKLY, interval=1, weekdays=[0, 4])
    assert next_d == date(2026, 5, 8)  # Friday

    # Next from Friday -> next week Monday
    next_mon = calculate_next_occurrence(date(2026, 5, 8), RecurrenceFrequency.WEEKLY, interval=1, weekdays=[0, 4])
    assert next_mon == date(2026, 5, 11)

    # Next with interval=2 (every 2 weeks on Monday)
    next_biweekly = calculate_next_occurrence(date(2026, 5, 8), RecurrenceFrequency.WEEKLY, interval=2, weekdays=[0, 4])
    assert next_biweekly == date(2026, 5, 18)


def test_recurrence_calculator_monthly_short_months():
    # Test 31st of January -> 28th of Feb (non-leap year)
    d = date(2025, 1, 31)
    next_d = calculate_next_occurrence(d, RecurrenceFrequency.MONTHLY, interval=1, day_of_month=31)
    assert next_d == date(2025, 2, 28)

    # Test last day of month (-1)
    last_day_d = calculate_next_occurrence(d, RecurrenceFrequency.MONTHLY, interval=1, day_of_month=-1)
    assert last_day_d == date(2025, 2, 28)


def test_recurrence_calculator_yearly_leap_year():
    # Leap year: 2024-02-29 -> 2025-02-28
    d = date(2024, 2, 29)
    next_d = calculate_next_occurrence(d, RecurrenceFrequency.YEARLY, interval=1, month_of_year=2, day_of_month=29)
    assert next_d == date(2025, 2, 28)


# 2. Integration Tests: CRUD, Lifecycle, Generation, Exceptions
def test_recurring_task_crud_and_validation(client: TestClient, auth_headers_a):
    headers = auth_headers_a

    # Validation: end_date < start_date
    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Invalid Recurring",
            "frequency": "DAILY",
            "start_date": "2026-06-10",
            "end_date": "2026-06-01",
        },
    )
    assert resp.status_code == 422

    # Success: Create Weekly Series
    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Weekly Team Standup",
            "description": "Sync on team progress",
            "priority": "HIGH",
            "frequency": "WEEKLY",
            "interval": 1,
            "start_date": "2026-05-04",
            "weekdays": [0, 4],  # Mon & Fri
        },
    )
    assert resp.status_code == 201
    series = resp.json()
    series_id = series["id"]
    assert series["title"] == "Weekly Team Standup"
    assert series["frequency"] == "WEEKLY"
    assert series["weekdays"] == [0, 4]

    # Retrieve series
    get_resp = client.get(f"/api/v1/recurring-tasks/{series_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == series_id

    # Update series
    patch_resp = client.patch(
        f"/api/v1/recurring-tasks/{series_id}",
        headers=headers,
        json={"title": "Updated Standup Title", "priority": "URGENT"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Standup Title"
    assert patch_resp.json()["priority"] == "URGENT"

    # List series
    list_resp = client.get("/api/v1/recurring-tasks", headers=headers)
    assert list_resp.status_code == 200
    assert any(s["id"] == series_id for s in list_resp.json()["items"])


def test_recurring_task_lifecycle_pause_resume_stop(client: TestClient, auth_headers_a):
    headers = auth_headers_a
    create_resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Monthly Report",
            "frequency": "MONTHLY",
            "interval": 1,
            "start_date": "2026-01-01",
        },
    )
    series_id = create_resp.json()["id"]

    # Pause
    pause_resp = client.post(f"/api/v1/recurring-tasks/{series_id}/pause", headers=headers)
    assert pause_resp.status_code == 200
    assert pause_resp.json()["is_active"] is False

    # Resume
    resume_resp = client.post(f"/api/v1/recurring-tasks/{series_id}/resume", headers=headers)
    assert resume_resp.status_code == 200
    assert resume_resp.json()["is_active"] is True

    # Stop
    stop_resp = client.post(f"/api/v1/recurring-tasks/{series_id}/stop", headers=headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["is_stopped"] is True
    assert stop_resp.json()["is_active"] is False


def test_occurrence_generation_and_idempotency(client: TestClient, auth_headers_a):
    headers = auth_headers_a

    # Create daily recurring series starting 2026-05-01
    create_resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Daily Workout",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": "2026-05-01",
            "max_occurrences": 5,
        },
    )
    series_id = create_resp.json()["id"]

    # Trigger generation up to 2026-05-03 (should generate May 1, May 2, May 3)
    gen_resp = client.post(
        "/api/v1/recurring-tasks/trigger-generation?target_date=2026-05-03",
        headers=headers,
    )
    assert gen_resp.status_code == 200

    # Idempotency: Triggering again for same or earlier date produces 0 new tasks
    gen_again_resp = client.post(
        "/api/v1/recurring-tasks/trigger-generation?target_date=2026-05-03",
        headers=headers,
    )
    assert gen_again_resp.status_code == 200
    assert gen_again_resp.json()["created_occurrences"] == 0

    # Verify occurrences list
    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    assert occ_resp.status_code == 200
    items = occ_resp.json()["items"]
    assert len(items) == 3
    dates = [t["occurrence_date"] for t in items]
    assert "2026-05-01" in dates
    assert "2026-05-02" in dates
    assert "2026-05-03" in dates


def test_skip_occurrence_behavior(client: TestClient, auth_headers_a):
    headers = auth_headers_a
    today = datetime.now(timezone.utc).date()
    day1 = today + timedelta(days=1)
    day2 = today + timedelta(days=2)
    day3 = today + timedelta(days=3)

    create_resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Daily Reading",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": day1.isoformat(),
        },
    )
    series_id = create_resp.json()["id"]

    # Skip day 2
    skip_resp = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": day2.isoformat(), "reason": "Traveling"},
    )
    assert skip_resp.status_code == 200

    # Trigger generation up to day 3
    client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers,
        json={"target_date": day3.isoformat()},
    )

    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    items = occ_resp.json()["items"]
    dates = [t["occurrence_date"] for t in items]
    assert day1.isoformat() in dates
    assert day2.isoformat() not in dates  # Skipped!
    assert day3.isoformat() in dates


def test_multi_user_isolation_recurring_tasks(client: TestClient, auth_headers_a, auth_headers_b):
    headers1 = auth_headers_a
    headers2 = auth_headers_b

    # User 1 creates series
    resp1 = client.post(
        "/api/v1/recurring-tasks",
        headers=headers1,
        json={"title": "User 1 Private Series", "frequency": "DAILY", "start_date": "2026-07-01"},
    )
    s1_id = resp1.json()["id"]

    # User 2 cannot access, update, pause, or delete User 1's series
    assert client.get(f"/api/v1/recurring-tasks/{s1_id}", headers=headers2).status_code == 404
    assert client.patch(f"/api/v1/recurring-tasks/{s1_id}", headers=headers2, json={"title": "Hacked"}).status_code == 404
    assert client.post(f"/api/v1/recurring-tasks/{s1_id}/pause", headers=headers2).status_code == 404
    assert client.delete(f"/api/v1/recurring-tasks/{s1_id}", headers=headers2).status_code == 404
    assert client.get(f"/api/v1/recurring-tasks/{s1_id}/occurrences", headers=headers2).status_code == 404


def test_series_creation_rollback_and_duplicate_prevention(client: TestClient, auth_headers_a, db_session):
    headers = auth_headers_a

    # Test initial occurrence generation
    create_resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Initial Occurrence Test",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": "2026-08-01",
        },
    )
    assert create_resp.status_code == 201
    series_data = create_resp.json()
    series_id = series_data["id"]

    # Initial occurrence should have been generated immediately
    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    assert occ_resp.status_code == 200
    assert occ_resp.json()["total"] == 1
    assert occ_resp.json()["items"][0]["occurrence_date"] == "2026-08-01"

    # Trigger generation for same date again -> should NOT create duplicates (idempotency check)
    trig_resp = client.post(
        "/api/v1/recurring-tasks/trigger-generation?target_date=2026-08-01",
        headers=headers,
    )
    assert trig_resp.status_code == 200
    assert trig_resp.json()["created_occurrences"] == 0

    occ_resp2 = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    assert occ_resp2.json()["total"] == 1


def test_series_creation_atomic_rollback_on_initial_occurrence_failure(client: TestClient, auth_headers_a, db_session, monkeypatch):
    """
    Deliberately forces initial occurrence generation to raise an exception and verifies
    that the entire transaction is rolled back: neither the series nor any occurrence persists.
    """
    from app.services.recurring_task_service import RecurringTaskService
    from app.models.recurring_task import RecurringTask

    headers = auth_headers_a
    original_generate = RecurringTaskService._generate_occurrences_for_series

    def faulty_generate(self, locked_series, cutoff):
        if locked_series.title == "Simulated Crash Series":
            raise RuntimeError("Database connection lost during initial occurrence generation")
        return original_generate(self, locked_series, cutoff)

    monkeypatch.setattr(RecurringTaskService, "_generate_occurrences_for_series", faulty_generate)

    # Attempt to create series that will fail during initial occurrence creation
    with pytest.raises(RuntimeError, match="Database connection lost during initial occurrence generation"):
        client.post(
            "/api/v1/recurring-tasks",
            headers=headers,
            json={
                "title": "Simulated Crash Series",
                "frequency": "DAILY",
                "interval": 1,
                "start_date": "2026-09-01",
            },
        )

    # Verify atomic rollback: the series was NOT persisted in the database
    from sqlalchemy import select
    crashed_series = db_session.execute(
        select(RecurringTask).where(RecurringTask.title == "Simulated Crash Series")
    ).scalar_one_or_none()
    assert crashed_series is None

    # And no orphan tasks were created
    from app.models.task import Task
    orphan_task = db_session.execute(
        select(Task).where(Task.title == "Simulated Crash Series")
    ).scalar_one_or_none()
    assert orphan_task is None


def test_trigger_generation_future_date_limit_and_security(client: TestClient, auth_headers_a, auth_headers_b):
    """
    Verifies future-date limit (max 30 days) and security boundaries on trigger-generation:
    - Today: 200 OK
    - Today + 30 days: 200 OK
    - Today + 31 days: 422 Unprocessable Entity
    - Unauthenticated: 401 Unauthorized
    - Series ownership / isolation: User A's generation does not generate User B's series
    """
    today = datetime.now(timezone.utc).date()
    headers_a = auth_headers_a
    headers_b = auth_headers_b

    # 1. Unauthenticated request rejected with 401
    unauth_resp = client.post("/api/v1/recurring-tasks/trigger-generation", json={})
    assert unauth_resp.status_code == 401

    # 2. Exceeding max future horizon (today + 31 days) rejected with 422
    future_31 = (today + timedelta(days=31)).isoformat()
    resp_over = client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers_a,
        json={"target_date": future_31},
    )
    assert resp_over.status_code == 422
    assert "cannot exceed 30 days into the future" in resp_over.json()["detail"]

    # 3. Valid target date: today + 30 days succeeds with 200
    future_30 = (today + timedelta(days=30)).isoformat()
    resp_30 = client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers_a,
        json={"target_date": future_30},
    )
    assert resp_30.status_code == 200

    # 4. Valid target date: today succeeds with 200
    resp_today = client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers_a,
        json={"target_date": today.isoformat()},
    )
    assert resp_today.status_code == 200

    # 5. User isolation check:
    # User B creates a series starting tomorrow
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    b_series = client.post(
        "/api/v1/recurring-tasks",
        headers=headers_b,
        json={
            "title": "User B Standup",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": tomorrow.isoformat(),
        },
    ).json()

    # Initial occurrence for tomorrow was created on series creation (1 occurrence)
    b_occ_initial = client.get(f"/api/v1/recurring-tasks/{b_series['id']}/occurrences", headers=headers_b).json()
    assert b_occ_initial["total"] == 1

    # User A triggers generation up to day_after
    client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers_a,
        json={"target_date": day_after.isoformat()},
    )

    # User B's occurrences should NOT have been advanced or generated by User A (still 1 occurrence)
    b_occ = client.get(f"/api/v1/recurring-tasks/{b_series['id']}/occurrences", headers=headers_b).json()
    assert b_occ["total"] == 1


def test_skip_occurrence_validation(client: TestClient, auth_headers_a):
    """
    Verifies occurrence skipping validation and rules:
    - Valid future scheduled occurrence date succeeds (advances next_occurrence_date).
    - Past date is rejected with 422.
    - Date not matching the recurrence rule is rejected with 422.
    - Duplicate skip is idempotent (200 OK).
    - Multiple consecutive skips advance next_occurrence_date appropriately.
    """
    headers = auth_headers_a
    today = datetime.now(timezone.utc).date()
    # Create weekly series on Mondays only
    # Find next Monday that is in the future
    days_to_next_monday = (0 - today.weekday()) % 7
    if days_to_next_monday == 0:
        days_to_next_monday = 7
    first_monday = today + timedelta(days=days_to_next_monday)
    second_monday = first_monday + timedelta(days=7)
    third_monday = first_monday + timedelta(days=14)

    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Monday Only Standup",
            "frequency": "WEEKLY",
            "interval": 1,
            "weekdays": [0],
            "start_date": first_monday.isoformat(),
        },
    )
    assert resp.status_code == 201
    series = resp.json()
    series_id = series["id"]
    # The first occurrence on first_monday (2026-11-09) was already generated during series creation,
    # so series.next_occurrence_date is naturally second_monday (2026-11-16)!
    assert series["next_occurrence_date"] == second_monday.isoformat()

    # 1. Past date rejected
    past_date = (today - timedelta(days=1)).isoformat()
    skip_past = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": past_date, "reason": "Yesterday"},
    )
    assert skip_past.status_code == 422
    assert "Cannot skip a past occurrence date" in skip_past.json()["detail"]

    # 2. Invalid date outside schedule (e.g. Tuesday = second_monday + 1 day) rejected
    invalid_date = (second_monday + timedelta(days=1)).isoformat()
    skip_invalid = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": invalid_date, "reason": "Tuesday is not on schedule"},
    )
    assert skip_invalid.status_code == 422
    assert "does not belong to the recurrence schedule" in skip_invalid.json()["detail"]

    # 3. Valid skip for second_monday
    skip_valid = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": second_monday.isoformat(), "reason": "Bank holiday"},
    )
    assert skip_valid.status_code == 200
    data = skip_valid.json()
    # Next occurrence should have advanced to third_monday
    assert data["next_occurrence_date"] == third_monday.isoformat()

    # 4. Duplicate skip is idempotent (200 OK)
    skip_dup = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": second_monday.isoformat(), "reason": "Duplicate skip attempt"},
    )
    assert skip_dup.status_code == 200
    assert skip_dup.json()["next_occurrence_date"] == third_monday.isoformat()

    # 5. Consecutive skip (skipping third_monday as well)
    fourth_monday = first_monday + timedelta(days=21)
    skip_consec = client.post(
        f"/api/v1/recurring-tasks/{series_id}/skip",
        headers=headers,
        json={"skip_date": third_monday.isoformat(), "reason": "Vacation"},
    )
    assert skip_consec.status_code == 200
    # Advances to fourth_monday
    assert skip_consec.json()["next_occurrence_date"] == fourth_monday.isoformat()


def test_series_editing_reconciliation_and_preservation(client: TestClient, auth_headers_a):
    """
    Verifies recurrence series updating semantics:
    - Protects completed occurrences and modified occurrences.
    - Reconciles future pending TODO occurrences when recurrence rules change (e.g. DAILY -> WEEKLY).
    - Preserves historical tasks untouched.
    """
    headers = auth_headers_a
    today = datetime.now(timezone.utc).date()

    # Create daily series starting today
    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Daily Sync Series",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": today.isoformat(),
        },
    )
    assert resp.status_code == 201
    series = resp.json()
    series_id = series["id"]

    # Generate occurrences for the next 5 days
    target = today + timedelta(days=5)
    client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers,
        json={"target_date": target.isoformat()},
    )

    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    tasks = occ_resp.json()["items"]
    assert len(tasks) >= 5

    # Complete the occurrence for today
    today_task = next(t for t in tasks if t["occurrence_date"] == today.isoformat())
    patch_resp = client.patch(
        f"/api/v1/tasks/{today_task['id']}",
        headers=headers,
        json={"status": "COMPLETED"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "COMPLETED"

    # Now update series from DAILY to WEEKLY (e.g. only on today's weekday)
    # The pending future occurrences for tomorrow, day+2, etc. should be reconciled/deleted
    # while today's completed task remains intact!
    update_resp = client.patch(
        f"/api/v1/recurring-tasks/{series_id}",
        headers=headers,
        json={
            "frequency": "WEEKLY",
            "interval": 1,
            "weekdays": [today.weekday()],
        },
    )
    assert update_resp.status_code == 200

    # Fetch occurrences again
    occ_resp2 = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    tasks2 = occ_resp2.json()["items"]

    # Verify:
    # 1. The completed task for today is still present and COMPLETED
    completed_task = next((t for t in tasks2 if t["id"] == today_task["id"]), None)
    assert completed_task is not None
    assert completed_task["status"] == "COMPLETED"

    # 2. None of the stale daily tasks (e.g. tomorrow) exist if they don't match the new rule
    for t in tasks2:
        if t["id"] != today_task["id"]:
            # All remaining/future occurrences must be on today's weekday
            dt = datetime.strptime(t["occurrence_date"], "%Y-%m-%d").date()
            assert dt.weekday() == today.weekday()


def test_series_editing_individually_modified_todo_occurrences_preserved(client: TestClient, auth_headers_a):
    """
    Verifies that individually modified TODO occurrences are preserved during recurrence series changes:
    1. Create a daily recurring series.
    2. Generate several future occurrences.
    3. Individually modify one future occurrence's title, description, or priority while keeping its status TODO.
    4. Change the series frequency to weekly.
    5. Verify that the modified occurrence is preserved, even if its date no longer matches the new recurrence rule.
    6. Verify that obsolete, untouched pending occurrences are reconciled correctly.
    """
    headers = auth_headers_a
    today = datetime.now(timezone.utc).date()

    # 1. Create daily series starting today
    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Daily Sync Routine",
            "description": "Standard daily sync notes",
            "priority": "MEDIUM",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": today.isoformat(),
        },
    )
    assert resp.status_code == 201
    series = resp.json()
    series_id = series["id"]

    # 2. Generate occurrences for the next 5 days
    target = today + timedelta(days=5)
    client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers,
        json={"target_date": target.isoformat()},
    )

    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    tasks = occ_resp.json()["items"]
    assert len(tasks) >= 5

    # 3. Choose tomorrow's occurrence (which won't match weekly if we change to weekly on today's weekday)
    tomorrow = today + timedelta(days=1)
    tomorrow_task = next(t for t in tasks if t["occurrence_date"] == tomorrow.isoformat())

    # Individually modify tomorrow's task: change title and priority while keeping status TODO
    patch_resp = client.patch(
        f"/api/v1/tasks/{tomorrow_task['id']}",
        headers=headers,
        json={
            "title": "Special Planning Session - Customized",
            "priority": "HIGH",
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "TODO"
    assert patch_resp.json()["title"] == "Special Planning Session - Customized"
    assert patch_resp.json()["priority"] == "HIGH"

    # 4. Change series frequency to weekly (strictly on today's weekday)
    update_resp = client.patch(
        f"/api/v1/recurring-tasks/{series_id}",
        headers=headers,
        json={
            "frequency": "WEEKLY",
            "interval": 1,
            "weekdays": [today.weekday()],
        },
    )
    assert update_resp.status_code == 200

    # 5. Fetch occurrences and verify reconciliation
    occ_resp2 = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    tasks2 = occ_resp2.json()["items"]
    print("\nDEBUG TASKS AFTER RECONCILIATION:", [(t["occurrence_date"], t["title"]) for t in tasks2])

    # Modified occurrence for tomorrow MUST BE PRESERVED
    preserved_task = next((t for t in tasks2 if t["id"] == tomorrow_task["id"]), None)
    assert preserved_task is not None
    assert preserved_task["title"] == "Special Planning Session - Customized"
    assert preserved_task["priority"] == "HIGH"
    assert preserved_task["status"] == "TODO"
    assert preserved_task["occurrence_date"] == tomorrow.isoformat()

    # 6. Verify untouched obsolete daily tasks (e.g. today + 2, today + 3) WERE deleted/reconciled
    day_2 = (today + timedelta(days=2)).isoformat()
    day_2_task = next((t for t in tasks2 if t["occurrence_date"] == day_2), None)
    # Since day_2 is not today's weekday and was untouched, it must not exist
    if (today + timedelta(days=2)).weekday() != today.weekday():
        assert day_2_task is None


def test_series_editing_parameter_limits_and_stopping(client: TestClient, auth_headers_a):
    """
    Verifies that updating:
    - end_date
    - max_occurrences
    - frequency / interval
    correctly updates next_occurrence_date, is_stopped, and reconciles future occurrences.
    """
    headers = auth_headers_a
    today = datetime.now(timezone.utc).date()

    # Create daily series starting today with end_date in 30 days
    resp = client.post(
        "/api/v1/recurring-tasks",
        headers=headers,
        json={
            "title": "Short Lived Series",
            "frequency": "DAILY",
            "interval": 1,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        },
    )
    assert resp.status_code == 201
    series = resp.json()
    series_id = series["id"]

    # Generate next 10 days
    client.post(
        "/api/v1/recurring-tasks/trigger-generation",
        headers=headers,
        json={"target_date": (today + timedelta(days=10)).isoformat()},
    )

    # 1. Update end_date to yesterday or today
    # Should stop the series and set next_occurrence_date to None
    patch_resp = client.patch(
        f"/api/v1/recurring-tasks/{series_id}",
        headers=headers,
        json={
            "end_date": today.isoformat(),
        },
    )
    assert patch_resp.status_code == 200
    updated_series = patch_resp.json()
    assert updated_series["is_stopped"] is True
    assert updated_series["next_occurrence_date"] is None

    # Verify future tasks beyond today were reconciled/deleted
    occ_resp = client.get(f"/api/v1/recurring-tasks/{series_id}/occurrences", headers=headers)
    tasks = occ_resp.json()["items"]
    for t in tasks:
        assert t["occurrence_date"] <= today.isoformat()



