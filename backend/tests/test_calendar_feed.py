import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.calendar_event import CalendarEvent
from app.models.category import Category
from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.recurring_task import RecurrenceFrequency, RecurringTask, RecurringTaskSkip
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="feed_user_a@example.com",
        display_name="Feed User A",
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
        email="feed_user_b@example.com",
        display_name="Feed User B",
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


# ---------------------------------------------------------
# Feed Overlap and Filtering Tests
# ---------------------------------------------------------

def test_unified_feed_overlap_and_ordering(
    client: TestClient,
    db_session,
    user_a: User,
    auth_headers_a: dict,
):
    """
    Test calendar feed with timed events, all-day events, task deadlines,
    overlap conditions (before, crossing, after), and deterministic sorting.
    """
    range_start = datetime(2026, 11, 10, 0, 0, 0, tzinfo=timezone.utc)
    range_end = datetime(2026, 11, 20, 0, 0, 0, tzinfo=timezone.utc)

    # 1. Event inside range
    ev_inside = CalendarEvent(
        user_id=user_a.id,
        title="Inside Range Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 12, 11, 0, tzinfo=timezone.utc),
        timezone="UTC",
    )

    # 2. Event overlapping start boundary (starts before 11-10, ends after 11-10)
    ev_overlap_start = CalendarEvent(
        user_id=user_a.id,
        title="Overlap Start Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 9, 20, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc),
        timezone="UTC",
    )

    # 3. Event overlapping end boundary (starts before 11-20, ends after 11-20)
    ev_overlap_end = CalendarEvent(
        user_id=user_a.id,
        title="Overlap End Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 19, 22, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 20, 4, 0, tzinfo=timezone.utc),
        timezone="UTC",
    )

    # 4. Event completely before range
    ev_before = CalendarEvent(
        user_id=user_a.id,
        title="Before Range Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 8, 11, 0, tzinfo=timezone.utc),
        timezone="UTC",
    )

    # 5. Event completely after range
    ev_after = CalendarEvent(
        user_id=user_a.id,
        title="After Range Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 21, 11, 0, tzinfo=timezone.utc),
        timezone="UTC",
    )

    # 6. All-day event inside range
    ev_allday = CalendarEvent(
        user_id=user_a.id,
        title="All Day Workshop",
        is_all_day=True,
        start_date=date(2026, 11, 15),
        end_date=date(2026, 11, 17),
        timezone="UTC",
    )

    # 7. Task with due_date inside range
    task_inside = Task(
        user_id=user_a.id,
        title="Submit Report",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        due_date=datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc),
    )

    # 8. Task with due_date outside range
    task_outside = Task(
        user_id=user_a.id,
        title="Future Task",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        due_date=datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc),
    )

    # 9. Task with null due_date (should never appear in calendar feed)
    task_no_due = Task(
        user_id=user_a.id,
        title="Backlog Item",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        due_date=None,
    )

    db_session.add_all([
        ev_inside,
        ev_overlap_start,
        ev_overlap_end,
        ev_before,
        ev_after,
        ev_allday,
        task_inside,
        task_outside,
        task_no_due,
    ])
    db_session.commit()

    res = client.get(
        f"/api/v1/calendar/feed?start={range_start.isoformat()}&end={range_end.isoformat()}&timezone=UTC",
        headers=auth_headers_a,
    )
    if res.status_code != 200:
        print("ERROR DETAIL:", res.json())
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 5  # ev_inside, ev_overlap_start, ev_overlap_end, ev_allday, task_inside

    titles = [item["title"] for item in data["items"]]
    assert "Overlap Start Event" in titles
    assert "Inside Range Event" in titles
    assert "Submit Report" in titles
    assert "All Day Workshop" in titles
    assert "Overlap End Event" in titles
    assert "Before Range Event" not in titles
    assert "After Range Event" not in titles
    assert "Future Task" not in titles
    assert "Backlog Item" not in titles

    # Verify item types
    item_types = {item["title"]: item["type"] for item in data["items"]}
    assert item_types["Submit Report"] == "task_deadline"
    assert item_types["Inside Range Event"] == "event"
    assert item_types["All Day Workshop"] == "event"


def test_feed_filters_project_category_status(
    client: TestClient,
    db_session,
    user_a: User,
    auth_headers_a: dict,
):
    """Test filtering calendar feed by project, category, status, and include flags."""
    range_start = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
    range_end = datetime(2026, 11, 30, 0, 0, 0, tzinfo=timezone.utc)

    proj = Project(user_id=user_a.id, name="Q4 Launch", status=ProjectStatus.ACTIVE)
    cat = Category(user_id=user_a.id, name="Marketing", name_normalized="marketing", color="#EF4444")
    db_session.add_all([proj, cat])
    db_session.commit()
    db_session.refresh(proj)
    db_session.refresh(cat)

    task_matching = Task(
        user_id=user_a.id,
        title="Marketing Task",
        project_id=proj.id,
        category_id=cat.id,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
    )
    task_other = Task(
        user_id=user_a.id,
        title="Dev Task",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        due_date=datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc),
    )
    event_standalone = CalendarEvent(
        user_id=user_a.id,
        title="Standalone Event",
        is_all_day=False,
        start_at=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 17, 11, 0, tzinfo=timezone.utc),
    )
    db_session.add_all([task_matching, task_other, event_standalone])
    db_session.commit()

    # 1. Filter by project_id -> returns matching task only
    res_proj = client.get(
        f"/api/v1/calendar/feed?start={range_start.isoformat()}&end={range_end.isoformat()}&project_id={proj.id}",
        headers=auth_headers_a,
    )
    assert res_proj.status_code == status.HTTP_200_OK
    assert res_proj.json()["total"] == 1
    assert res_proj.json()["items"][0]["title"] == "Marketing Task"

    # 2. Disable include_tasks -> only event_standalone returns
    res_no_tasks = client.get(
        f"/api/v1/calendar/feed?start={range_start.isoformat()}&end={range_end.isoformat()}&include_tasks=false",
        headers=auth_headers_a,
    )
    assert res_no_tasks.status_code == status.HTTP_200_OK
    assert res_no_tasks.json()["total"] == 1
    assert res_no_tasks.json()["items"][0]["title"] == "Standalone Event"

    # 3. Disable include_events -> only tasks return
    res_no_events = client.get(
        f"/api/v1/calendar/feed?start={range_start.isoformat()}&end={range_end.isoformat()}&include_events=false",
        headers=auth_headers_a,
    )
    assert res_no_events.status_code == status.HTTP_200_OK
    assert res_no_events.json()["total"] == 2


def test_feed_recurring_task_occurrences(
    client: TestClient,
    db_session,
    user_a: User,
    auth_headers_a: dict,
):
    """Test that materialized recurring task occurrences are returned cleanly without duplicates."""
    series = RecurringTask(
        user_id=user_a.id,
        title="Weekly Sprint Review",
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        start_date=date(2026, 11, 1),
    )
    db_session.add(series)
    db_session.commit()
    db_session.refresh(series)

    # Materialized occurrence 1
    occ1 = Task(
        user_id=user_a.id,
        recurring_task_id=series.id,
        occurrence_date=date(2026, 11, 8),
        occurrence_index=1,
        title="Weekly Sprint Review",
        status=TaskStatus.COMPLETED,
        priority=TaskPriority.MEDIUM,
        due_date=datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc),
    )
    # Materialized occurrence 2
    occ2 = Task(
        user_id=user_a.id,
        recurring_task_id=series.id,
        occurrence_date=date(2026, 11, 15),
        occurrence_index=2,
        title="Weekly Sprint Review",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc),
    )
    db_session.add_all([occ1, occ2])
    db_session.commit()

    range_start = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
    range_end = datetime(2026, 11, 30, 0, 0, 0, tzinfo=timezone.utc)

    # Recurring only filter
    res = client.get(
        f"/api/v1/calendar/feed?start={range_start.isoformat()}&end={range_end.isoformat()}&recurring_only=true",
        headers=auth_headers_a,
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["type"] == "task_deadline"
        assert item["recurring_task_id"] == str(series.id)
        assert item["occurrence_date"] is not None


# ---------------------------------------------------------
# Task Scheduling Endpoint Tests
# ---------------------------------------------------------

def test_schedule_task_endpoint(
    client: TestClient,
    db_session,
    user_a: User,
    user_b: User,
    auth_headers_a: dict,
    auth_headers_b: dict,
):
    """Test scheduling time blocks for an existing task, custom titles, multiple time blocks, and security."""
    task = Task(
        user_id=user_a.id,
        title="Write Documentation",
        description="Write Stage 3B docs",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        due_date=datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    start_1 = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)
    end_1 = datetime(2026, 11, 18, 11, 0, tzinfo=timezone.utc)

    # 1. Schedule first time block (defaults to task title)
    res1 = client.post(
        "/api/v1/calendar/events/schedule-task",
        json={
            "task_id": str(task.id),
            "start_at": start_1.isoformat(),
            "end_at": end_1.isoformat(),
            "timezone": "UTC",
        },
        headers=auth_headers_a,
    )
    assert res1.status_code == status.HTTP_201_CREATED
    data1 = res1.json()
    assert data1["title"] == "Write Documentation"
    assert data1["task_id"] == str(task.id)
    assert data1["is_all_day"] is False

    # 2. Schedule second time block for same task with custom title and location
    start_2 = datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc)
    end_2 = datetime(2026, 11, 19, 16, 0, tzinfo=timezone.utc)
    res2 = client.post(
        "/api/v1/calendar/events/schedule-task",
        json={
            "task_id": str(task.id),
            "title": "Docs Final Review",
            "start_at": start_2.isoformat(),
            "end_at": end_2.isoformat(),
            "timezone": "America/New_York",
            "location": "Zoom Room",
        },
        headers=auth_headers_a,
    )
    assert res2.status_code == status.HTTP_201_CREATED
    data2 = res2.json()
    assert data2["title"] == "Docs Final Review"
    assert data2["task_id"] == str(task.id)

    # 3. Verify original task is untouched
    db_session.refresh(task)
    assert task.title == "Write Documentation"
    assert task.status == TaskStatus.TODO
    expected_due = datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)
    actual_due = task.due_date if task.due_date.tzinfo else task.due_date.replace(tzinfo=timezone.utc)
    assert actual_due == expected_due

    # 4. User B cannot schedule User A's task -> 404
    res_b = client.post(
        "/api/v1/calendar/events/schedule-task",
        json={
            "task_id": str(task.id),
            "start_at": start_1.isoformat(),
            "end_at": end_1.isoformat(),
        },
        headers=auth_headers_b,
    )
    assert res_b.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# Date Range & Timezone Boundary Validation Tests
# ---------------------------------------------------------

def test_feed_date_range_and_timezone_validation(client: TestClient, auth_headers_a: dict):
    """Test validation of start/end datetime offsets, end <= start, max 93 days, and timezone."""
    # 1. Missing timezone offset
    res1 = client.get(
        "/api/v1/calendar/feed?start=2026-11-01T00:00:00&end=2026-11-10T00:00:00Z",
        headers=auth_headers_a,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. End before start
    res2 = client.get(
        "/api/v1/calendar/feed?start=2026-11-10T00:00:00Z&end=2026-11-05T00:00:00Z",
        headers=auth_headers_a,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. Exceeds 93 days window
    res3 = client.get(
        "/api/v1/calendar/feed?start=2026-01-01T00:00:00Z&end=2026-06-01T00:00:00Z",
        headers=auth_headers_a,
    )
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "93 days" in res3.json()["detail"]

    # 4. Invalid IANA timezone
    res4 = client.get(
        "/api/v1/calendar/feed?start=2026-11-01T00:00:00Z&end=2026-11-10T00:00:00Z&timezone=Fake/Timezone",
        headers=auth_headers_a,
    )
    assert res4.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid IANA timezone" in res4.json()["detail"]
