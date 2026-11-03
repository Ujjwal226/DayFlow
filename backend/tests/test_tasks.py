from datetime import datetime, timedelta, timezone
import pytest
from app.core.security import create_access_token, hash_password
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="user_a@example.com",
        display_name="User Alpha",
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
        email="user_b@example.com",
        display_name="User Beta",
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


# --- Basic CRUD & Validation Tests ---

def test_create_task_success(client, auth_headers_a, user_a):
    payload = {
        "title": "Complete Stage 2 Implementation",
        "description": "Design and build task management system.",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "start_date": datetime.now(timezone.utc).isoformat(),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    }
    res = client.post("/api/v1/tasks", json=payload, headers=auth_headers_a)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["priority"] == "HIGH"
    assert data["status"] == "IN_PROGRESS"
    assert data["user_id"] == str(user_a.id)
    assert data["is_archived"] is False
    assert data["is_overdue"] is False
    assert data["completed_at"] is None


def test_create_task_empty_title_validation(client, auth_headers_a):
    res = client.post("/api/v1/tasks", json={"title": "   "}, headers=auth_headers_a)
    assert res.status_code == 422


def test_create_task_due_before_start_validation(client, auth_headers_a):
    now = datetime.now(timezone.utc)
    payload = {
        "title": "Invalid Date Task",
        "start_date": (now + timedelta(days=2)).isoformat(),
        "due_date": now.isoformat(),
    }
    res = client.post("/api/v1/tasks", json=payload, headers=auth_headers_a)
    assert res.status_code == 422


def test_get_task_success(client, auth_headers_a, user_a, db_session):
    task = Task(
        user_id=user_a.id,
        title="Sample Task A",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
    )
    db_session.add(task)
    db_session.commit()

    res = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["id"] == str(task.id)
    assert res.json()["title"] == "Sample Task A"


def test_update_task_status_completes_and_reopens(client, auth_headers_a, user_a, db_session):
    task = Task(
        user_id=user_a.id,
        title="Lifecycle Task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )
    db_session.add(task)
    db_session.commit()

    # Move to COMPLETED: completed_at must be populated
    res_completed = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"status": "COMPLETED"},
        headers=auth_headers_a,
    )
    assert res_completed.status_code == 200
    assert res_completed.json()["status"] == "COMPLETED"
    assert res_completed.json()["completed_at"] is not None

    # Move back to IN_PROGRESS: completed_at must be cleared
    res_reopened = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers_a,
    )
    assert res_reopened.status_code == 200
    assert res_reopened.json()["status"] == "IN_PROGRESS"
    assert res_reopened.json()["completed_at"] is None


def test_delete_task(client, auth_headers_a, user_a, db_session):
    task = Task(
        user_id=user_a.id,
        title="To Be Deleted",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
    )
    db_session.add(task)
    db_session.commit()

    res_del = client.delete(f"/api/v1/tasks/{task.id}", headers=auth_headers_a)
    assert res_del.status_code == 200

    # Ensure 404 after deletion
    res_get = client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers_a)
    assert res_get.status_code == 404


def test_duplicate_task(client, auth_headers_a, user_a, db_session):
    task = Task(
        user_id=user_a.id,
        title="Original Template",
        description="Copy this description",
        status=TaskStatus.COMPLETED,
        completed_at=datetime.now(timezone.utc),
        is_archived=True,
        priority=TaskPriority.HIGH,
    )
    db_session.add(task)
    db_session.commit()

    res = client.post(f"/api/v1/tasks/{task.id}/duplicate", headers=auth_headers_a)
    assert res.status_code == 201
    dup = res.json()
    assert dup["id"] != str(task.id)
    assert dup["title"] == "Original Template (Copy)"
    assert dup["description"] == task.description
    assert dup["status"] == "TODO"  # Reset
    assert dup["completed_at"] is None  # Reset
    assert dup["is_archived"] is False  # Reset
    assert dup["priority"] == "HIGH"


def test_archive_and_restore_task(client, auth_headers_a, user_a, db_session):
    task = Task(
        user_id=user_a.id,
        title="Archive Target",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
    )
    db_session.add(task)
    db_session.commit()

    # Archive
    res_archive = client.patch(f"/api/v1/tasks/{task.id}/archive", headers=auth_headers_a)
    assert res_archive.status_code == 200
    assert res_archive.json()["is_archived"] is True

    # Restore
    res_restore = client.patch(f"/api/v1/tasks/{task.id}/restore", headers=auth_headers_a)
    assert res_restore.status_code == 200
    assert res_restore.json()["is_archived"] is False


def test_task_filters_search_and_pagination(client, auth_headers_a, user_a, db_session):
    # Create several tasks
    now = datetime.now(timezone.utc)
    t1 = Task(user_id=user_a.id, title="Alpha Task Urgent", status=TaskStatus.TODO, priority=TaskPriority.URGENT)
    t2 = Task(user_id=user_a.id, title="Beta Task Normal", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM)
    t3 = Task(user_id=user_a.id, title="Gamma Task Low", status=TaskStatus.COMPLETED, priority=TaskPriority.LOW)
    t4 = Task(user_id=user_a.id, title="Archived Delta", status=TaskStatus.TODO, priority=TaskPriority.HIGH, is_archived=True)
    db_session.add_all([t1, t2, t3, t4])
    db_session.commit()

    # Default list excludes archived
    res_default = client.get("/api/v1/tasks", headers=auth_headers_a)
    assert res_default.status_code == 200
    data = res_default.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # Status filter
    res_status = client.get("/api/v1/tasks?status=TODO", headers=auth_headers_a)
    assert res_status.json()["total"] == 1
    assert res_status.json()["items"][0]["title"] == "Alpha Task Urgent"

    # Priority filter
    res_priority = client.get("/api/v1/tasks?priority=URGENT", headers=auth_headers_a)
    assert res_priority.json()["total"] == 1

    # Search filter
    res_search = client.get("/api/v1/tasks?search=Beta", headers=auth_headers_a)
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["title"] == "Beta Task Normal"

    # Archived filter
    res_archived = client.get("/api/v1/tasks?is_archived=true", headers=auth_headers_a)
    assert res_archived.json()["total"] == 1
    assert res_archived.json()["items"][0]["title"] == "Archived Delta"


def test_task_statistics_and_dynamic_overdue(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    # 1 Overdue TODO task
    t_overdue = Task(
        user_id=user_a.id,
        title="Overdue Task",
        status=TaskStatus.TODO,
        due_date=now - timedelta(days=2),
    )
    # 1 Upcoming IN_PROGRESS task
    t_upcoming = Task(
        user_id=user_a.id,
        title="Upcoming Task",
        status=TaskStatus.IN_PROGRESS,
        due_date=now + timedelta(days=2),
    )
    # 1 Completed task (even if past due date, should not count as overdue)
    t_completed = Task(
        user_id=user_a.id,
        title="Completed Task",
        status=TaskStatus.COMPLETED,
        due_date=now - timedelta(days=1),
        completed_at=now,
    )
    # 1 Cancelled task
    t_cancelled = Task(
        user_id=user_a.id,
        title="Cancelled Task",
        status=TaskStatus.CANCELLED,
    )
    # 1 Archived task (should not count in active statistics)
    t_archived = Task(
        user_id=user_a.id,
        title="Archived Task",
        status=TaskStatus.TODO,
        is_archived=True,
    )
    db_session.add_all([t_overdue, t_upcoming, t_completed, t_cancelled, t_archived])
    db_session.commit()

    res = client.get("/api/v1/tasks/statistics", headers=auth_headers_a)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total"] == 4
    assert stats["todo"] == 1
    assert stats["in_progress"] == 1
    assert stats["completed"] == 1
    assert stats["cancelled"] == 1
    assert stats["overdue"] == 1
    assert stats["upcoming"] == 1


# --- Critical Multi-User Isolation Tests ---

def test_multi_user_isolation_full_matrix(client, auth_headers_a, auth_headers_b, user_a, user_b, db_session):
    """
    Assert that User A cannot retrieve, update, delete, duplicate,
    archive, or restore User B's task, returning 404 and leaking zero data.
    """
    # Create task owned strictly by User B
    task_b = Task(
        user_id=user_b.id,
        title="User B Secret Task",
        description="Private information of User B",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )
    db_session.add(task_b)
    db_session.commit()

    # 1. User A tries to GET User B's task -> 404
    res_get = client.get(f"/api/v1/tasks/{task_b.id}", headers=auth_headers_a)
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Task not found."

    # 2. User A tries to PATCH User B's task -> 404
    res_patch = client.patch(
        f"/api/v1/tasks/{task_b.id}",
        json={"title": "Hacked Title"},
        headers=auth_headers_a,
    )
    assert res_patch.status_code == 404

    # 3. User A tries to DELETE User B's task -> 404
    res_delete = client.delete(f"/api/v1/tasks/{task_b.id}", headers=auth_headers_a)
    assert res_delete.status_code == 404

    # 4. User A tries to DUPLICATE User B's task -> 404
    res_duplicate = client.post(f"/api/v1/tasks/{task_b.id}/duplicate", headers=auth_headers_a)
    assert res_duplicate.status_code == 404

    # 5. User A tries to ARCHIVE User B's task -> 404
    res_archive = client.patch(f"/api/v1/tasks/{task_b.id}/archive", headers=auth_headers_a)
    assert res_archive.status_code == 404

    # 6. User A tries to RESTORE User B's task -> 404
    res_restore = client.patch(f"/api/v1/tasks/{task_b.id}/restore", headers=auth_headers_a)
    assert res_restore.status_code == 404

    # 7. User A listing tasks does not see User B's task
    res_list = client.get("/api/v1/tasks", headers=auth_headers_a)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 0
    assert len(res_list.json()["items"]) == 0

    # 8. User B CAN access their own task
    res_b_get = client.get(f"/api/v1/tasks/{task_b.id}", headers=auth_headers_b)
    assert res_b_get.status_code == 200
    assert res_b_get.json()["title"] == "User B Secret Task"


# --- Regression Tests for Date Validation & Cross-Field Checks ---

def test_patch_task_update_start_date_later_than_existing_due_date_fails(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    task = Task(
        user_id=user_a.id,
        title="Initial Valid Task",
        start_date=now,
        due_date=now + timedelta(days=2),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Attempt to update start_date to after due_date (now + 5 days) without touching due_date
    res = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"start_date": (now + timedelta(days=5)).isoformat()},
        headers=auth_headers_a,
    )
    assert res.status_code == 422
    assert "Due date cannot be earlier than start date." in res.json()["detail"]

    # Verify task in DB remains completely unmodified
    db_session.refresh(task)
    stored_start = task.start_date.replace(tzinfo=timezone.utc) if task.start_date.tzinfo is None else task.start_date
    stored_due = task.due_date.replace(tzinfo=timezone.utc) if task.due_date.tzinfo is None else task.due_date
    assert stored_start.timestamp() == pytest.approx(now.timestamp(), abs=1)
    assert stored_due.timestamp() == pytest.approx((now + timedelta(days=2)).timestamp(), abs=1)


def test_patch_task_update_due_date_earlier_than_existing_start_date_fails(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    task = Task(
        user_id=user_a.id,
        title="Initial Valid Task 2",
        start_date=now + timedelta(days=3),
        due_date=now + timedelta(days=5),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Attempt to update due_date to earlier than start_date (now + 1 day) without touching start_date
    res = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"due_date": (now + timedelta(days=1)).isoformat()},
        headers=auth_headers_a,
    )
    assert res.status_code == 422
    assert "Due date cannot be earlier than start date." in res.json()["detail"]

    # Verify database state was not partially modified
    db_session.refresh(task)
    stored_start = task.start_date.replace(tzinfo=timezone.utc) if task.start_date.tzinfo is None else task.start_date
    stored_due = task.due_date.replace(tzinfo=timezone.utc) if task.due_date.tzinfo is None else task.due_date
    assert stored_start.timestamp() == pytest.approx((now + timedelta(days=3)).timestamp(), abs=1)
    assert stored_due.timestamp() == pytest.approx((now + timedelta(days=5)).timestamp(), abs=1)


def test_patch_task_clearing_either_date_succeeds(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    task = Task(
        user_id=user_a.id,
        title="Task To Clear Dates",
        start_date=now,
        due_date=now + timedelta(days=2),
    )
    db_session.add(task)
    db_session.commit()

    # Clear due_date
    res_due = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"due_date": None},
        headers=auth_headers_a,
    )
    assert res_due.status_code == 200
    assert res_due.json()["due_date"] is None
    assert res_due.json()["start_date"] is not None

    # Clear start_date as well
    res_start = client.patch(
        f"/api/v1/tasks/{task.id}",
        json={"start_date": None},
        headers=auth_headers_a,
    )
    assert res_start.status_code == 200
    assert res_start.json()["start_date"] is None
    assert res_start.json()["due_date"] is None


# --- Regression Tests for Pagination, Sorting, and Window Filtering ---

def test_pagination_and_sorting_query_validation(client, auth_headers_a):
    # Invalid sort field
    res_invalid_field = client.get("/api/v1/tasks?sort_by=not_a_field", headers=auth_headers_a)
    assert res_invalid_field.status_code == 422

    # Invalid sort order
    res_invalid_order = client.get("/api/v1/tasks?sort_order=sideways", headers=auth_headers_a)
    assert res_invalid_order.status_code == 422

    # Excessive page size (> 100)
    res_large_page = client.get("/api/v1/tasks?page_size=101", headers=auth_headers_a)
    assert res_large_page.status_code == 422


def test_statistics_upcoming_window(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)

    # 1. Task due in 3 days (within upcoming 7-day window)
    task_upcoming = Task(
        user_id=user_a.id,
        title="Upcoming in 3 days",
        status=TaskStatus.TODO,
        due_date=now + timedelta(days=3),
    )
    # 2. Task due in 10 days (outside upcoming 7-day window)
    task_future = Task(
        user_id=user_a.id,
        title="Future in 10 days",
        status=TaskStatus.TODO,
        due_date=now + timedelta(days=10),
    )
    # 3. Completed task due in 2 days (should not be in upcoming)
    task_completed = Task(
        user_id=user_a.id,
        title="Completed upcoming",
        status=TaskStatus.COMPLETED,
        due_date=now + timedelta(days=2),
    )
    # 4. Archived task due in 2 days (should not be counted)
    task_archived = Task(
        user_id=user_a.id,
        title="Archived upcoming",
        status=TaskStatus.TODO,
        due_date=now + timedelta(days=2),
        is_archived=True,
    )
    db_session.add_all([task_upcoming, task_future, task_completed, task_archived])
    db_session.commit()

    res = client.get("/api/v1/tasks/statistics", headers=auth_headers_a)
    assert res.status_code == 200
    stats = res.json()
    assert stats["upcoming"] == 1
    assert stats["total"] == 3  # Non-archived: upcoming + future + completed


