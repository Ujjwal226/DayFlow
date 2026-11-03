import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.project import ProjectPriority, ProjectStatus
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="proj_user_a@example.com",
        display_name="Project User A",
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
        email="proj_user_b@example.com",
        display_name="Project User B",
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


def test_project_crud_and_validation(client: TestClient, auth_headers_a):
    """Test project creation, retrieval, update, dates validation, and listing."""
    headers = auth_headers_a

    # 1. Invalid date validation (due_date < start_date)
    resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Invalid Project",
            "start_date": "2026-06-10",
            "due_date": "2026-06-01",
        },
    )
    assert resp.status_code == 422

    # 2. Empty name validation
    resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "   "},
    )
    assert resp.status_code == 422

    # 3. Create project successfully
    resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "DayFlow Redesign",
            "description": "Revamping UI/UX components",
            "status": "ACTIVE",
            "priority": "HIGH",
            "start_date": "2026-06-01",
            "due_date": "2026-06-30",
            "color": "#10B981",
        },
    )
    assert resp.status_code == 201
    proj_data = resp.json()
    proj_id = proj_data["id"]
    assert proj_data["name"] == "DayFlow Redesign"
    assert proj_data["status"] == "ACTIVE"
    assert proj_data["priority"] == "HIGH"
    assert proj_data["color"] == "#10B981"
    assert proj_data["statistics"]["total_tasks"] == 0
    assert proj_data["statistics"]["completion_percentage"] == 0.0

    # 4. Retrieve project
    resp = client.get(f"/api/v1/projects/{proj_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == proj_id

    # 5. Partial update with date check against existing start_date
    resp = client.patch(
        f"/api/v1/projects/{proj_id}",
        headers=headers,
        json={"due_date": "2026-05-15"},  # earlier than existing start_date 2026-06-01
    )
    assert resp.status_code == 422

    # Valid update
    resp = client.patch(
        f"/api/v1/projects/{proj_id}",
        headers=headers,
        json={"name": "DayFlow 2.0 Redesign", "due_date": "2026-07-15"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "DayFlow 2.0 Redesign"
    assert resp.json()["due_date"] == "2026-07-15"

    # 6. List projects
    resp = client.get("/api/v1/projects", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(p["id"] == proj_id for p in items)


def test_project_archive_and_restore(client: TestClient, auth_headers_a):
    """Test archiving and restoring projects."""
    headers = auth_headers_a

    create_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Archive Test Project"},
    )
    proj_id = create_resp.json()["id"]

    # Archive project
    resp = client.patch(f"/api/v1/projects/{proj_id}/archive", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_archived"] is True

    # Excluded from active list by default
    resp = client.get("/api/v1/projects", headers=headers)
    assert all(p["id"] != proj_id for p in resp.json()["items"])

    # Included when is_archived=true
    resp = client.get("/api/v1/projects?is_archived=true", headers=headers)
    assert any(p["id"] == proj_id for p in resp.json()["items"])

    # Restore project
    resp = client.patch(f"/api/v1/projects/{proj_id}/restore", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_archived"] is False

    # Visible again in default active list
    resp = client.get("/api/v1/projects", headers=headers)
    assert any(p["id"] == proj_id for p in resp.json()["items"])


def test_project_task_assignment_and_statistics(client: TestClient, auth_headers_a):
    """
    Test task assignment to projects, task removal, subtask exclusion,
    archived task exclusion, and progress calculation.
    """
    headers = auth_headers_a

    # Create project
    proj_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Analytics Dashboard"},
    )
    proj_id = proj_resp.json()["id"]

    # Zero-task project progress is 0.0%
    stats_resp = client.get(f"/api/v1/projects/{proj_id}/statistics", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_tasks"] == 0
    assert stats["completion_percentage"] == 0.0

    # Create task 1: TODO
    t1_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Design Database Schema", "status": "TODO"},
    )
    t1_id = t1_resp.json()["id"]

    # Create task 2: COMPLETED
    t2_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Setup Repositories", "status": "COMPLETED"},
    )
    t2_id = t2_resp.json()["id"]

    # Assign task 1 and task 2 to project
    r1 = client.put(f"/api/v1/projects/{proj_id}/tasks/{t1_id}", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["project_id"] == proj_id

    r2 = client.put(f"/api/v1/projects/{proj_id}/tasks/{t2_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["project_id"] == proj_id

    # Check project tasks list
    task_list_resp = client.get(f"/api/v1/projects/{proj_id}/tasks", headers=headers)
    assert task_list_resp.status_code == 200
    assert task_list_resp.json()["total"] == 2

    # Check project statistics: 2 total, 1 completed -> 50%
    stats_resp = client.get(f"/api/v1/projects/{proj_id}/statistics", headers=headers)
    stats = stats_resp.json()
    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 1
    assert stats["pending_tasks"] == 1
    assert stats["completion_percentage"] == 50.0

    # Add a subtask to Task 1: Subtasks should be excluded from project task count
    subtask_resp = client.post(
        f"/api/v1/tasks/{t1_id}/subtasks",
        headers=headers,
        json={"title": "Create Foreign Key Migration", "status": "COMPLETED"},
    )
    assert subtask_resp.status_code == 201
    st_id = subtask_resp.json()["id"]

    # Trying to assign a subtask directly to a project must fail
    st_assign_resp = client.put(f"/api/v1/projects/{proj_id}/tasks/{st_id}", headers=headers)
    assert st_assign_resp.status_code == 422

    # Project stats must still count only the 2 top-level tasks
    stats = client.get(f"/api/v1/projects/{proj_id}/statistics", headers=headers).json()
    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 1

    # Archive task 2: Archived tasks should be excluded from active project statistics
    client.patch(f"/api/v1/tasks/{t2_id}/archive", headers=headers)
    stats = client.get(f"/api/v1/projects/{proj_id}/statistics", headers=headers).json()
    assert stats["total_tasks"] == 1
    assert stats["completed_tasks"] == 0
    assert stats["completion_percentage"] == 0.0

    # Restore task 2
    client.patch(f"/api/v1/tasks/{t2_id}/restore", headers=headers)

    # Remove task 1 from project
    del_resp = client.delete(f"/api/v1/projects/{proj_id}/tasks/{t1_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["project_id"] is None

    stats = client.get(f"/api/v1/projects/{proj_id}/statistics", headers=headers).json()
    assert stats["total_tasks"] == 1
    assert stats["completed_tasks"] == 1
    assert stats["completion_percentage"] == 100.0


def test_project_deletion_preserves_tasks(client: TestClient, auth_headers_a):
    """Verify that deleting a project unlinks tasks and sets project_id to NULL without deleting tasks."""
    headers = auth_headers_a

    # Create project and task
    proj_resp = client.post("/api/v1/projects", headers=headers, json={"name": "Temporary Project"})
    proj_id = proj_resp.json()["id"]

    task_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Preserved Task", "project_id": proj_id},
    )
    task_id = task_resp.json()["id"]
    assert task_resp.json()["project_id"] == proj_id

    # Delete project
    del_proj_resp = client.delete(f"/api/v1/projects/{proj_id}", headers=headers)
    assert del_proj_resp.status_code == 204

    # Verify task still exists and project_id is None
    get_task_resp = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert get_task_resp.status_code == 200
    assert get_task_resp.json()["project_id"] is None


def test_multi_user_isolation_projects(client: TestClient, auth_headers_a, auth_headers_b):
    """Verify complete isolation: users cannot access, update, delete or assign cross-user projects/tasks."""
    headers1 = auth_headers_a
    headers2 = auth_headers_b

    # User 1 creates project and task
    p1_resp = client.post("/api/v1/projects", headers=headers1, json={"name": "User 1 Secret Project"})
    p1_id = p1_resp.json()["id"]

    t1_resp = client.post("/api/v1/tasks", headers=headers1, json={"title": "User 1 Task"})
    t1_id = t1_resp.json()["id"]

    # User 2 creates project and task
    p2_resp = client.post("/api/v1/projects", headers=headers2, json={"name": "User 2 Project"})
    p2_id = p2_resp.json()["id"]

    t2_resp = client.post("/api/v1/tasks", headers=headers2, json={"title": "User 2 Task"})
    t2_id = t2_resp.json()["id"]

    # 1. User 2 cannot get User 1's project
    resp = client.get(f"/api/v1/projects/{p1_id}", headers=headers2)
    assert resp.status_code == 404

    # 2. User 2 cannot update User 1's project
    resp = client.patch(f"/api/v1/projects/{p1_id}", headers=headers2, json={"name": "Hacked"})
    assert resp.status_code == 404

    # 3. User 2 cannot delete User 1's project
    resp = client.delete(f"/api/v1/projects/{p1_id}", headers=headers2)
    assert resp.status_code == 404

    # 4. User 2 cannot list User 1's project tasks
    resp = client.get(f"/api/v1/projects/{p1_id}/tasks", headers=headers2)
    assert resp.status_code == 404

    # 5. User 1 cannot assign User 2's task to User 1's project
    resp = client.put(f"/api/v1/projects/{p1_id}/tasks/{t2_id}", headers=headers1)
    assert resp.status_code == 404

    # 6. User 2 cannot assign User 1's task to User 2's project
    resp = client.put(f"/api/v1/projects/{p2_id}/tasks/{t1_id}", headers=headers2)
    assert resp.status_code == 404

    # 7. Creating task with foreign project_id fails
    resp = client.post(
        "/api/v1/tasks",
        headers=headers1,
        json={"title": "Illegal Task", "project_id": p2_id},
    )
    assert resp.status_code == 404
