import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.goal import Goal, GoalCategory, GoalMilestone, GoalPriority, GoalStatus, GoalType, ProgressCalculationMethod
from app.models.project import Project, ProjectPriority, ProjectStatus
from app.models.reminder import Notification
from app.models.task import Task
from app.models.user import User
from app.services.goal_service import GoalService


@pytest.fixture
def user_a(db_session: Session):
    user = User(
        email="goal_user_a@example.com",
        display_name="Goal User A",
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
        email="goal_user_b@example.com",
        display_name="Goal User B",
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


def test_goal_crud_lifecycle_and_ownership(client: TestClient, db_session: Session, user_a: User, user_b: User, auth_headers_a, auth_headers_b):
    # 1. Create a goal for User A
    create_payload = {
        "title": "Learn Rust in 90 Days",
        "description": "Master systems programming and concurrency",
        "category": "LEARNING",
        "goal_type": "OUTCOME",
        "priority": "HIGH",
        "status": "NOT_STARTED",
        "progress_method": "MANUAL",
        "progress_percentage": 10.0,
        "target_date": str(date.today() + timedelta(days=90)),
    }
    resp = client.post("/api/v1/goals", headers=auth_headers_a, json=create_payload)
    assert resp.status_code == 201
    goal = resp.json()
    assert goal["title"] == "Learn Rust in 90 Days"
    assert goal["progress_percentage"] == 10.0
    goal_id = goal["id"]

    # 2. User B cannot access User A's goal
    resp_b = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers_b)
    assert resp_b.status_code == 404

    # 3. Update goal
    update_payload = {
        "title": "Learn Rust and WebAssembly",
        "progress_percentage": 25.5,
        "status": "IN_PROGRESS",
    }
    resp_update = client.patch(f"/api/v1/goals/{goal_id}", headers=auth_headers_a, json=update_payload)
    assert resp_update.status_code == 200
    assert resp_update.json()["title"] == "Learn Rust and WebAssembly"
    assert resp_update.json()["progress_percentage"] == 25.5
    assert resp_update.json()["status"] == "IN_PROGRESS"

    # 4. Check activities audit
    resp_act = client.get(f"/api/v1/goals/{goal_id}/activities", headers=auth_headers_a)
    assert resp_act.status_code == 200
    assert len(resp_act.json()) >= 2  # CREATED and UPDATED

    # 5. Complete and reopen
    resp_complete = client.post(f"/api/v1/goals/{goal_id}/complete", headers=auth_headers_a)
    assert resp_complete.status_code == 200
    assert resp_complete.json()["status"] == "COMPLETED"
    assert resp_complete.json()["progress_percentage"] == 100.0

    resp_reopen = client.post(f"/api/v1/goals/{goal_id}/reopen", headers=auth_headers_a)
    assert resp_reopen.status_code == 200
    assert resp_reopen.json()["status"] == "IN_PROGRESS"

    # 6. Delete goal
    resp_del = client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers_a)
    assert resp_del.status_code == 204
    resp_get_deleted = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers_a)
    assert resp_get_deleted.status_code == 404


def test_milestone_management_and_progress_calculation(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # Create milestone-based goal
    create_payload = {
        "title": "Publish Technical Book",
        "category": "CAREER",
        "goal_type": "MILESTONE",
        "progress_method": "MILESTONE",
        "priority": "MEDIUM",
        "status": "NOT_STARTED",
    }
    resp = client.post("/api/v1/goals", headers=auth_headers_a, json=create_payload)
    assert resp.status_code == 201
    goal_id = resp.json()["id"]

    # Add 2 milestones
    m1 = client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        headers=auth_headers_a,
        json={"title": "Draft Table of Contents", "order_index": 1},
    ).json()
    m2 = client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        headers=auth_headers_a,
        json={"title": "Complete Chapter 1", "order_index": 2},
    ).json()

    # Progress is initially 0%
    goal_check = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers_a).json()
    assert goal_check["milestone_count"] == 2
    assert goal_check["progress_percentage"] == 0.0

    # Complete 1 milestone -> progress automatically becomes 50%
    client.patch(f"/api/v1/goals/milestones/{m1['id']}", headers=auth_headers_a, json={"is_completed": True})
    goal_half = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers_a).json()
    assert goal_half["progress_percentage"] == 50.0

    # Complete second milestone -> progress 100% and goal auto-completes
    client.patch(f"/api/v1/goals/milestones/{m2['id']}", headers=auth_headers_a, json={"is_completed": True})
    goal_full = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers_a).json()
    assert goal_full["progress_percentage"] == 100.0
    assert goal_full["status"] == "COMPLETED"

    # Reorder milestones
    reorder_resp = client.post(
        f"/api/v1/goals/{goal_id}/milestones/reorder",
        headers=auth_headers_a,
        json=[{"id": m2["id"], "order_index": 1}, {"id": m1["id"], "order_index": 2}],
    )
    assert reorder_resp.status_code == 200
    assert reorder_resp.json()[0]["id"] == m2["id"]


def test_numeric_measurable_goal_progress(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    create_payload = {
        "title": "Emergency Fund",
        "category": "FINANCE",
        "goal_type": "NUMERIC",
        "progress_method": "NUMERIC",
        "target_value": 10000.0,
        "current_value": 2500.0,
        "unit": "USD",
        "status": "IN_PROGRESS",
    }
    resp = client.post("/api/v1/goals", headers=auth_headers_a, json=create_payload)
    assert resp.status_code == 201
    goal = resp.json()
    assert goal["progress_percentage"] == 25.0

    # Update current value
    goal_id = goal["id"]
    update_resp = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=auth_headers_a,
        json={"current_value": 7500.0},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["progress_percentage"] == 75.0


def test_task_and_project_linking_and_cross_user_security(
    client: TestClient, db_session: Session, user_a: User, user_b: User, auth_headers_a, auth_headers_b
):
    # Setup project and task for User A
    proj_a = Project(user_id=user_a.id, name="User A Architecture", status=ProjectStatus.ACTIVE, priority=ProjectPriority.HIGH)
    db_session.add(proj_a)
    task_a = Task(user_id=user_a.id, title="Implement Schema")
    db_session.add(task_a)

    # Setup task for User B
    task_b = Task(user_id=user_b.id, title="User B Private Task")
    db_session.add(task_b)
    db_session.commit()

    # User A creates goal linked to project and task
    create_payload = {
        "title": "Architecture Upgrade",
        "category": "PROJECTS",
        "project_id": str(proj_a.id),
        "linked_task_ids": [str(task_a.id)],
    }
    resp = client.post("/api/v1/goals", headers=auth_headers_a, json=create_payload)
    assert resp.status_code == 201
    goal = resp.json()
    assert goal["project_name"] == "User A Architecture"
    assert goal["linked_task_count"] == 1
    assert goal["linked_tasks"][0]["title"] == "Implement Schema"
    goal_id = goal["id"]

    # User A tries to link User B's task -> 404
    resp_cross = client.post(
        f"/api/v1/goals/{goal_id}/tasks",
        headers=auth_headers_a,
        json={"task_id": str(task_b.id)},
    )
    assert resp_cross.status_code == 404

    # Unlink task
    resp_unlink = client.delete(f"/api/v1/goals/{goal_id}/tasks/{task_a.id}", headers=auth_headers_a)
    assert resp_unlink.status_code == 200
    assert resp_unlink.json()["linked_task_count"] == 0


def test_planning_objectives_daily_weekly_monthly(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    today = date.today()

    # Create daily objective
    daily_payload = {
        "period_type": "DAILY",
        "period_date": str(today),
        "title": "Ship Stage 3G Goals Module",
        "priority": "HIGH",
    }
    resp = client.post("/api/v1/goals/planning/objectives", headers=auth_headers_a, json=daily_payload)
    assert resp.status_code == 201
    obj = resp.json()
    assert obj["title"] == "Ship Stage 3G Goals Module"
    obj_id = obj["id"]

    # Query daily summary
    summary_resp = client.get(
        "/api/v1/goals/planning/summary",
        headers=auth_headers_a,
        params={"period_type": "DAILY", "period_date": str(today)},
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_objectives"] == 1
    assert summary["completed_objectives"] == 0
    assert summary["completion_rate"] == 0.0

    # Mark completed
    patch_resp = client.patch(
        f"/api/v1/goals/planning/objectives/{obj_id}",
        headers=auth_headers_a,
        json={"is_completed": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_completed"] is True

    # Check updated summary
    summary_done = client.get(
        "/api/v1/goals/planning/summary",
        headers=auth_headers_a,
        params={"period_type": "DAILY", "period_date": str(today)},
    ).json()
    assert summary_done["completed_objectives"] == 1
    assert summary_done["completion_rate"] == 100.0


def test_goal_analytics_aggregation(client: TestClient, db_session: Session, user_a: User, auth_headers_a):
    # Query analytics overview
    analytics_resp = client.get("/api/v1/goals/analytics", headers=auth_headers_a)
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    assert "active_goals" in data
    assert "categories" in data
    assert "completion_rate" in data
    assert "goals_completed_over_time" in data
    assert "overdue_goals" in data
    assert "average_completion_time_days" in data
    assert "monthly_planning_completion_rate" in data


def test_reopen_goal_preserves_manual_progress(client: TestClient, user_a: User, auth_headers_a):
    # Create goal with manual progress at 75%
    create_resp = client.post(
        "/api/v1/goals",
        headers=auth_headers_a,
        json={
            "title": "Manual Goal Reopen Test",
            "progress_method": "MANUAL",
            "progress_percentage": 75.0,
        },
    )
    assert create_resp.status_code == 201
    goal_id = create_resp.json()["id"]

    # Complete it explicitly
    comp_resp = client.post(f"/api/v1/goals/{goal_id}/complete", headers=auth_headers_a)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "COMPLETED"
    assert comp_resp.json()["progress_percentage"] == 100.0

    # Reopen it - must NOT silently overwrite to 90%, should remain at user's state
    reopen_resp = client.post(f"/api/v1/goals/{goal_id}/reopen", headers=auth_headers_a)
    assert reopen_resp.status_code == 200
    data = reopen_resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["completed_at"] is None
    # Progress is preserved (not arbitrarily set to 90.0)
    assert data["progress_percentage"] == 100.0


def test_goal_health_and_deterministic_status(db_session: Session, user_a: User):
    service = GoalService(db_session)
    today = date.today()

    # Past target date => AT_RISK
    goal_overdue = Goal(
        user_id=user_a.id,
        title="Overdue Goal",
        status=GoalStatus.IN_PROGRESS.value,
        progress_percentage=20.0,
        target_date=today - timedelta(days=2),
    )
    health = service.evaluate_goal_health(goal_overdue, as_of_date=today)
    assert health == GoalStatus.AT_RISK.value

    # Approaching target date within 7 days with < 50% progress => AT_RISK
    goal_approaching_low = Goal(
        user_id=user_a.id,
        title="Approaching Low Progress",
        status=GoalStatus.IN_PROGRESS.value,
        progress_percentage=30.0,
        target_date=today + timedelta(days=3),
    )
    health = service.evaluate_goal_health(goal_approaching_low, as_of_date=today)
    assert health == GoalStatus.AT_RISK.value

    # Approaching with >= 50% progress => ON_TRACK
    goal_approaching_good = Goal(
        user_id=user_a.id,
        title="Approaching Good Progress",
        status=GoalStatus.IN_PROGRESS.value,
        progress_percentage=80.0,
        target_date=today + timedelta(days=3),
    )
    health = service.evaluate_goal_health(goal_approaching_good, as_of_date=today)
    assert health == GoalStatus.ON_TRACK.value

    # Completed remains completed
    goal_completed = Goal(
        user_id=user_a.id,
        title="Completed Goal",
        status=GoalStatus.COMPLETED.value,
        progress_percentage=100.0,
        target_date=today - timedelta(days=5),
    )
    assert service.evaluate_goal_health(goal_completed, as_of_date=today) == GoalStatus.COMPLETED.value


def test_goal_and_milestone_notifications(db_session: Session, user_a: User):
    from app.services.scheduler_service import ReminderSchedulerService
    from app.models.reminder import NotificationPreference

    today = date.today()
    now = datetime.now(timezone.utc)

    # Enable preferences
    pref = NotificationPreference(
        user_id=user_a.id,
        in_app_enabled=True,
        email_enabled=True,
        due_date_reminders_enabled=True,
        overdue_reminders_enabled=True,
    )
    db_session.add(pref)

    # Create approaching goal (due in 1 day)
    goal_due = Goal(
        user_id=user_a.id,
        title="Launch Product 1.0",
        status=GoalStatus.IN_PROGRESS.value,
        progress_percentage=60.0,
        target_date=today + timedelta(days=1),
    )
    db_session.add(goal_due)
    db_session.commit()

    scheduler = ReminderSchedulerService(db_session)
    count = scheduler.process_goal_notifications(current_time=now)
    assert count >= 1

    # Check notification created
    notifs = db_session.query(Notification).filter(Notification.user_id == user_a.id).all()
    titles = [n.title for n in notifs]
    assert any("Goal Deadline Approaching" in t for t in titles)

    # Second pass should deduplicate and create 0 new notifications
    second_count = scheduler.process_goal_notifications(current_time=now)
    assert second_count == 0

    # Add a SECOND approaching goal - it must NOT be suppressed by the first goal's notification!
    # Goal due tomorrow (same due date as today+1 or within 2 days of today_date)
    goal_due_second = Goal(
        user_id=user_a.id,
        title="Deliver Sprint Milestone",
        status=GoalStatus.IN_PROGRESS.value,
        progress_percentage=40.0,
        target_date=now.date() + timedelta(days=1),
    )
    db_session.add(goal_due_second)
    db_session.commit()

    third_count = scheduler.process_goal_notifications(current_time=now)
    assert third_count == 1
