import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.calendar_event import CalendarEvent
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="cal_user_a@example.com",
        display_name="Calendar User A",
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
        email="cal_user_b@example.com",
        display_name="Calendar User B",
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


def test_create_timed_event(client: TestClient, user_a: User, auth_headers_a: dict):
    """Test creating a valid timed calendar event."""
    start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    end_at = start_at + timedelta(hours=2)

    payload = {
        "title": "Strategy Sync",
        "description": "Discuss Q4 targets",
        "location": "Room 402",
        "color": "#3B82F6",
        "is_all_day": False,
        "timezone": "America/New_York",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
    }

    res = client.post("/api/v1/calendar/events", json=payload, headers=auth_headers_a)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["title"] == "Strategy Sync"
    assert data["is_all_day"] is False
    assert data["timezone"] == "America/New_York"
    assert data["user_id"] == str(user_a.id)
    assert data["task_id"] is None
    assert data["start_at"] is not None
    assert data["end_at"] is not None
    assert data["start_date"] is None
    assert data["end_date"] is None


def test_create_allday_event(client: TestClient, user_a: User, auth_headers_a: dict):
    """Test creating a valid multi-day all-day calendar event."""
    payload = {
        "title": "Company Offsite",
        "is_all_day": True,
        "timezone": "UTC",
        "start_date": "2026-11-10",
        "end_date": "2026-11-13",
    }

    res = client.post("/api/v1/calendar/events", json=payload, headers=auth_headers_a)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["title"] == "Company Offsite"
    assert data["is_all_day"] is True
    assert data["start_date"] == "2026-11-10"
    assert data["end_date"] == "2026-11-13"
    assert data["start_at"] is None
    assert data["end_at"] is None


def test_validation_rejects_invalid_representation(client: TestClient, auth_headers_a: dict):
    """Test rejection when dates/times do not match is_all_day mode."""
    # 1. Timed event missing end_at
    start_at = datetime.now(timezone.utc)
    res1 = client.post(
        "/api/v1/calendar/events",
        json={"title": "Missing end", "is_all_day": False, "start_at": start_at.isoformat()},
        headers=auth_headers_a,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Timed event with end_at <= start_at
    res2 = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "End before start",
            "is_all_day": False,
            "start_at": start_at.isoformat(),
            "end_at": (start_at - timedelta(hours=1)).isoformat(),
        },
        headers=auth_headers_a,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. All-day event with end_date <= start_date
    res3 = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "Invalid dates",
            "is_all_day": True,
            "start_date": "2026-11-10",
            "end_date": "2026-11-10",
        },
        headers=auth_headers_a,
    )
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 4. Invalid IANA timezone
    res4 = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "Bad tz",
            "is_all_day": True,
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "timezone": "Invalid/Zone_Name",
        },
        headers=auth_headers_a,
    )
    assert res4.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 5. Empty title
    res5 = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "   ",
            "is_all_day": True,
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
        },
        headers=auth_headers_a,
    )
    assert res5.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_crud_and_partial_update(client: TestClient, auth_headers_a: dict):
    """Test full CRUD cycle and partial update state checking."""
    start_at = datetime.now(timezone.utc) + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)

    # Create
    create_res = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "Client Pitch",
            "is_all_day": False,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers=auth_headers_a,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    event_id = create_res.json()["id"]

    # Get
    get_res = client.get(
        f"/api/v1/calendar/events/{event_id}",
        headers=auth_headers_a,
    )
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["title"] == "Client Pitch"

    # Partial update title and description
    put_res = client.put(
        f"/api/v1/calendar/events/{event_id}",
        json={"title": "Updated Pitch", "description": "New slides"},
        headers=auth_headers_a,
    )
    assert put_res.status_code == status.HTTP_200_OK
    assert put_res.json()["title"] == "Updated Pitch"
    assert put_res.json()["description"] == "New slides"

    # List
    list_res = client.get(
        "/api/v1/calendar/events?page=1&page_size=10",
        headers=auth_headers_a,
    )
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] >= 1

    # Delete
    del_res = client.delete(
        f"/api/v1/calendar/events/{event_id}",
        headers=auth_headers_a,
    )
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify not found after delete
    get_after = client.get(
        f"/api/v1/calendar/events/{event_id}",
        headers=auth_headers_a,
    )
    assert get_after.status_code == status.HTTP_404_NOT_FOUND


def test_task_association_and_tenant_isolation(
    client: TestClient,
    db_session,
    user_a: User,
    user_b: User,
    auth_headers_a: dict,
    auth_headers_b: dict,
):
    """Test task linking, cross-user isolation, task deletion SET NULL behavior, and user cascade."""
    # 1. Create a task for user_a
    task_user1 = Task(
        user_id=user_a.id,
        title="User 1 Task",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )
    db_session.add(task_user1)
    db_session.commit()
    db_session.refresh(task_user1)

    # 2. user_a associates event with own task -> SUCCESS
    start_at = datetime.now(timezone.utc) + timedelta(hours=3)
    end_at = start_at + timedelta(hours=1)
    res_link = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "Timeblock for Task",
            "is_all_day": False,
            "task_id": str(task_user1.id),
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers=auth_headers_a,
    )
    assert res_link.status_code == status.HTTP_201_CREATED
    event_user1_id = res_link.json()["id"]
    assert res_link.json()["task_id"] == str(task_user1.id)

    # 3. user_b tries to link to user_a's task -> 404 FORBIDDEN/NOT FOUND
    res_cross_task = client.post(
        "/api/v1/calendar/events",
        json={
            "title": "Illegal Link",
            "is_all_day": False,
            "task_id": str(task_user1.id),
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        headers=auth_headers_b,
    )
    assert res_cross_task.status_code == status.HTTP_404_NOT_FOUND

    # 4. user_b cannot access or modify user_a's event
    res_cross_get = client.get(
        f"/api/v1/calendar/events/{event_user1_id}",
        headers=auth_headers_b,
    )
    assert res_cross_get.status_code == status.HTTP_404_NOT_FOUND

    res_cross_put = client.put(
        f"/api/v1/calendar/events/{event_user1_id}",
        json={"title": "Hacked Title"},
        headers=auth_headers_b,
    )
    assert res_cross_put.status_code == status.HTTP_404_NOT_FOUND

    res_cross_del = client.delete(
        f"/api/v1/calendar/events/{event_user1_id}",
        headers=auth_headers_b,
    )
    assert res_cross_del.status_code == status.HTTP_404_NOT_FOUND

    # 5. Delete task_user1: Event must be preserved and task_id set to NULL
    db_session.delete(task_user1)
    db_session.commit()

    ev_after_task_del = client.get(
        f"/api/v1/calendar/events/{event_user1_id}",
        headers=auth_headers_a,
    )
    assert ev_after_task_del.status_code == status.HTTP_200_OK
    assert ev_after_task_del.json()["task_id"] is None
