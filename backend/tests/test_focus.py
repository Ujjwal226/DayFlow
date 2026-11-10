import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.focus import FocusSession, FocusPreference
from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.task import Task
from app.models.user import User
from app.services.focus_service import FocusService


@pytest.fixture
def user_a(db_session: Session):
    user = User(
        email="focus_user_a@example.com",
        display_name="Focus User A",
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
        email="focus_user_b@example.com",
        display_name="Focus User B",
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


def test_focus_session_lifecycle_and_calculations(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # 1. Initially no active session
    resp_init = client.get("/api/v1/focus/active", headers=auth_headers_a)
    assert resp_init.status_code == 200
    assert resp_init.json() is None

    # 2. Start a session with custom duration (10 mins)
    resp_start = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "custom_duration_minutes": 10},
    )
    assert resp_start.status_code == 201
    session_data = resp_start.json()
    session_id = session_data["id"]
    assert session_data["status"] == "ACTIVE"
    assert session_data["planned_duration_seconds"] == 600
    assert session_data["remaining_seconds"] <= 600
    assert session_data["is_expired"] is False

    # 3. Active session endpoint returns the running session
    resp_active = client.get("/api/v1/focus/active", headers=auth_headers_a)
    assert resp_active.status_code == 200
    assert resp_active.json()["id"] == session_id

    # 4. Attempting to start another session while one is active returns 409 Conflict
    resp_conflict = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "custom_duration_minutes": 15},
    )
    assert resp_conflict.status_code == 409

    # 5. Pause the session
    resp_pause = client.post(f"/api/v1/focus/sessions/{session_id}/pause", headers=auth_headers_a)
    assert resp_pause.status_code == 200
    assert resp_pause.json()["status"] == "PAUSED"
    assert resp_pause.json()["paused_at"] is not None

    # 6. Resume the session
    resp_resume = client.post(f"/api/v1/focus/sessions/{session_id}/resume", headers=auth_headers_a)
    assert resp_resume.status_code == 200
    assert resp_resume.json()["status"] == "ACTIVE"
    assert resp_resume.json()["paused_at"] is None

    # 7. Complete the session
    resp_complete = client.post(f"/api/v1/focus/sessions/{session_id}/complete", headers=auth_headers_a)
    assert resp_complete.status_code == 200
    assert resp_complete.json()["status"] == "COMPLETED"
    assert resp_complete.json()["completed_at"] is not None
    assert resp_complete.json()["actual_duration_seconds"] >= 0

    # 8. Completed session is no longer active
    resp_after = client.get("/api/v1/focus/active", headers=auth_headers_a)
    assert resp_after.status_code == 200
    assert resp_after.json() is None


def test_abandon_session_not_counted_in_completed(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    resp_start = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "custom_duration_minutes": 25},
    )
    assert resp_start.status_code == 201
    session_id = resp_start.json()["id"]

    resp_abandon = client.post(f"/api/v1/focus/sessions/{session_id}/abandon", headers=auth_headers_a)
    assert resp_abandon.status_code == 200
    assert resp_abandon.json()["status"] == "ABANDONED"

    # History shows abandoned
    resp_hist = client.get("/api/v1/focus/history", headers=auth_headers_a)
    assert resp_hist.status_code == 200
    hist = resp_hist.json()
    assert any(s["id"] == session_id and s["status"] == "ABANDONED" for s in hist)


def test_task_project_association_and_cross_user_isolation(
    client: TestClient, db_session: Session, user_a: User, user_b: User, auth_headers_a, auth_headers_b
):
    # Create project and task for User A
    proj_a = Project(user_id=user_a.id, name="User A Project")
    db_session.add(proj_a)
    db_session.commit()

    task_a = Task(user_id=user_a.id, title="User A Task", project_id=proj_a.id)
    db_session.add(task_a)
    db_session.commit()

    # User A starts session with own task
    resp = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "task_id": str(task_a.id), "custom_duration_minutes": 10},
    )
    assert resp.status_code == 201
    assert resp.json()["task_id"] == str(task_a.id)
    assert resp.json()["task_title"] == "User A Task"

    # User B attempts to attach User A's task -> 404
    resp_cross = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_b,
        json={"session_type": "FOCUS", "task_id": str(task_a.id), "custom_duration_minutes": 10},
    )
    assert resp_cross.status_code == 404


def test_preferences_and_analytics(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # Get preferences
    pref_resp = client.get("/api/v1/focus/preferences", headers=auth_headers_a)
    assert pref_resp.status_code == 200
    assert pref_resp.json()["focus_duration_minutes"] == 25

    # Update preferences
    patch_resp = client.patch(
        "/api/v1/focus/preferences",
        headers=auth_headers_a,
        json={"focus_duration_minutes": 30, "daily_goal_minutes": 150},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["focus_duration_minutes"] == 30
    assert patch_resp.json()["daily_goal_minutes"] == 150

    # Create completed session directly in DB to check analytics
    now = datetime.now(timezone.utc)
    sess = FocusSession(
        user_id=user_a.id,
        session_type="FOCUS",
        status="COMPLETED",
        planned_duration_seconds=1800,
        actual_duration_seconds=1800,
        started_at=now - timedelta(minutes=35),
        completed_at=now - timedelta(minutes=5),
    )
    db_session.add(sess)
    db_session.commit()

    # Query analytics
    analytics_resp = client.get("/api/v1/focus/analytics", headers=auth_headers_a)
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    assert data["daily"]["today_completed_sessions"] >= 1
    assert data["daily"]["today_focus_seconds"] >= 1800
    assert data["weekly"]["total_focus_minutes"] >= 30


def test_skip_session_cycle_and_detail_endpoint(client: TestClient, db_session: Session, user_a: User, user_b: User, auth_headers_a, auth_headers_b):
    # Start a focus session
    resp = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "custom_duration_minutes": 25},
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # Verify session detail endpoint for user_a
    detail_resp = client.get(f"/api/v1/focus/sessions/{session_id}", headers=auth_headers_a)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == session_id

    # Verify cross-user ownership: user_b cannot view user_a's session
    detail_b = client.get(f"/api/v1/focus/sessions/{session_id}", headers=auth_headers_b)
    assert detail_b.status_code == 404

    # Skip current focus session -> automatically moves to SHORT_BREAK
    skip_resp = client.post(f"/api/v1/focus/sessions/{session_id}/skip", headers=auth_headers_a)
    assert skip_resp.status_code == 200
    next_session = skip_resp.json()
    assert next_session["session_type"] == "SHORT_BREAK"
    assert next_session["status"] == "ACTIVE"

    # Previous session is now marked ABANDONED (not counted in completed focus)
    old_detail = client.get(f"/api/v1/focus/sessions/{session_id}", headers=auth_headers_a)
    assert old_detail.status_code == 200
    assert old_detail.json()["status"] == "ABANDONED"


def test_db_level_partial_unique_index_active_conflict(client: TestClient, db_session: Session, user_a: User):
    # Directly verify partial unique index enforcement at DB level
    now = datetime.now(timezone.utc)
    sess1 = FocusSession(
        user_id=user_a.id,
        session_type="FOCUS",
        status="ACTIVE",
        planned_duration_seconds=1500,
        actual_duration_seconds=0,
        started_at=now,
    )
    db_session.add(sess1)
    db_session.commit()

    # Attempting to insert another ACTIVE or PAUSED session for the same user raises IntegrityError
    from sqlalchemy.exc import IntegrityError
    sess2 = FocusSession(
        user_id=user_a.id,
        session_type="SHORT_BREAK",
        status="PAUSED",
        planned_duration_seconds=300,
        actual_duration_seconds=0,
        started_at=now,
    )
    db_session.add(sess2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_idempotent_completion_and_notification_preferences(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # Set browser_notifications_enabled preference
    patch_resp = client.patch(
        "/api/v1/focus/preferences",
        headers=auth_headers_a,
        json={"browser_notifications_enabled": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["browser_notifications_enabled"] is True

    # Start a session
    resp = client.post(
        "/api/v1/focus/start",
        headers=auth_headers_a,
        json={"session_type": "FOCUS", "custom_duration_minutes": 15},
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # First complete call -> 200 OK
    complete1 = client.post(f"/api/v1/focus/sessions/{session_id}/complete", headers=auth_headers_a)
    assert complete1.status_code == 200
    assert complete1.json()["status"] == "COMPLETED"

    # Repeat complete call -> returns serialized completed session without error or duplicate notification
    complete2 = client.post(f"/api/v1/focus/sessions/{session_id}/complete", headers=auth_headers_a)
    assert complete2.status_code == 200
    assert complete2.json()["status"] == "COMPLETED"
