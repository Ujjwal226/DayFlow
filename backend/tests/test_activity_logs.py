import uuid
from datetime import datetime, timezone
import pytest
from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.models.task import Task
from app.models.user import User
from app.core.security import create_access_token, hash_password


@pytest.fixture
def user_a(db_session):
    user = User(
        email="user_a_act@example.com",
        display_name="User Alpha Activity",
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
        email="user_b_act@example.com",
        display_name="User Beta Activity",
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


def test_activity_logs_created_on_task_mutations(client, auth_headers_a):
    # 1. Create a task
    res_task = client.post(
        "/api/v1/tasks",
        json={"title": "Test Task Activity", "priority": "HIGH"},
        headers=auth_headers_a,
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]

    # 2. Check task activity timeline
    res_timeline = client.get(f"/api/v1/tasks/{task_id}/activity", headers=auth_headers_a)
    assert res_timeline.status_code == 200
    timeline = res_timeline.json()
    assert timeline["total"] >= 1
    assert any(log["action"] == ActivityAction.TASK_CREATED.value for log in timeline["items"])

    # 3. Update task (title & status)
    res_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated Task Activity", "status": "COMPLETED"},
        headers=auth_headers_a,
    )
    assert res_update.status_code == 200

    # 4. Check timeline has TASK_UPDATED and/or TASK_COMPLETED
    res_timeline2 = client.get(f"/api/v1/tasks/{task_id}/activity", headers=auth_headers_a)
    assert res_timeline2.status_code == 200
    actions = [log["action"] for log in res_timeline2.json()["items"]]
    assert ActivityAction.TASK_COMPLETED.value in actions or ActivityAction.TASK_UPDATED.value in actions

    # 5. Check global activity feed
    res_global = client.get("/api/v1/activity-logs", headers=auth_headers_a)
    assert res_global.status_code == 200
    global_items = res_global.json()["items"]
    assert len(global_items) >= 2


def test_multi_user_isolation_activity_logs(client, auth_headers_a, auth_headers_b):
    # User A creates a task
    res_a = client.post(
        "/api/v1/tasks",
        json={"title": "User A Private Task"},
        headers=auth_headers_a,
    )
    assert res_a.status_code == 201
    task_a_id = res_a.json()["id"]

    # User B cannot see User A's task timeline -> 404
    res_b_timeline = client.get(f"/api/v1/tasks/{task_a_id}/activity", headers=auth_headers_b)
    assert res_b_timeline.status_code == 404

    # User B's global feed does NOT contain User A's actions or task ID
    res_b_feed = client.get("/api/v1/activity-logs", headers=auth_headers_b)
    assert res_b_feed.status_code == 200
    for item in res_b_feed.json()["items"]:
        assert item.get("task_id") != task_a_id
        if item.get("extra_metadata"):
            assert item["extra_metadata"].get("title") != "User A Private Task"


def test_global_activity_feed_filters_and_pagination(client, auth_headers_a):
    # Create project and category to have distinct entity types
    res_cat = client.post("/api/v1/categories", json={"name": "Feed Cat Test", "color": "#0d9488"}, headers=auth_headers_a)
    assert res_cat.status_code == 201

    res_proj = client.post("/api/v1/projects", json={"name": "Feed Proj Test", "color": "#0d9488"}, headers=auth_headers_a)
    assert res_proj.status_code == 201

    # Filter by entity_type=PROJECT
    res_filter_proj = client.get("/api/v1/activity-logs?entity_type=PROJECT", headers=auth_headers_a)
    assert res_filter_proj.status_code == 200
    proj_logs = res_filter_proj.json()["items"]
    assert len(proj_logs) >= 1
    assert all(log["entity_type"] == "PROJECT" for log in proj_logs)

    # Filter by action=CATEGORY_CREATED
    res_filter_act = client.get("/api/v1/activity-logs?action=CATEGORY_CREATED", headers=auth_headers_a)
    assert res_filter_act.status_code == 200
    cat_logs = res_filter_act.json()["items"]
    assert len(cat_logs) >= 1
    assert all(log["action"] == "CATEGORY_CREATED" for log in cat_logs)

    # Pagination test
    res_paginated = client.get("/api/v1/activity-logs?page=1&page_size=2", headers=auth_headers_a)
    assert res_paginated.status_code == 200
    pdata = res_paginated.json()
    assert len(pdata["items"]) <= 2
    assert pdata["page"] == 1
    assert pdata["page_size"] == 2
    assert pdata["total"] >= 2


def test_deletion_preserves_activity_snapshot(client, auth_headers_a):
    # Create a task, then delete it
    res_task = client.post(
        "/api/v1/tasks",
        json={"title": "Task To Delete", "priority": "LOW"},
        headers=auth_headers_a,
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]

    res_del = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers_a)
    assert res_del.status_code == 200

    # Deleted task timeline returns 404
    res_timeline = client.get(f"/api/v1/tasks/{task_id}/activity", headers=auth_headers_a)
    assert res_timeline.status_code == 404

    # Global activity feed still has TASK_DELETED and the original TASK_CREATED
    res_global = client.get("/api/v1/activity-logs?action=TASK_DELETED", headers=auth_headers_a)
    assert res_global.status_code == 200
    items = res_global.json()["items"]
    print("ALL DELETED ITEMS RETURNED:", items)
    matching_deletes = [
        item for item in items
        if item.get("metadata") and item["metadata"].get("title") == "Task To Delete"
    ]
    assert len(matching_deletes) >= 1
    del_event = matching_deletes[0]
    assert del_event["entity_type"] == "TASK"
    assert del_event["action"] == "TASK_DELETED"
    assert del_event["metadata"]["title"] == "Task To Delete"


def test_subtask_activities_appear_in_task_timeline(client, auth_headers_a):
    # 1. Create parent task
    res_parent = client.post(
        "/api/v1/tasks",
        json={"title": "Parent Task For Subtasks"},
        headers=auth_headers_a,
    )
    assert res_parent.status_code == 201
    parent_id = res_parent.json()["id"]

    # 2. Add subtask
    res_sub = client.post(
        f"/api/v1/tasks/{parent_id}/subtasks",
        json={"title": "Subtask Item 1"},
        headers=auth_headers_a,
    )
    assert res_sub.status_code == 201
    sub_id = res_sub.json()["id"]

    # 3. Complete subtask via /api/v1/subtasks/{subtask_id}
    res_sub_update = client.patch(
        f"/api/v1/subtasks/{sub_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers_a,
    )
    assert res_sub_update.status_code == 200

    # 4. Check parent task activity timeline
    res_timeline = client.get(f"/api/v1/tasks/{parent_id}/activity", headers=auth_headers_a)
    assert res_timeline.status_code == 200
    timeline_items = res_timeline.json()["items"]
    sub_actions = [item["action"] for item in timeline_items if item["entity_type"] == "SUBTASK"]
    assert ActivityAction.SUBTASK_CREATED.value in sub_actions
    assert ActivityAction.SUBTASK_COMPLETED.value in sub_actions


def test_tag_assignment_and_removal_activity_logs(client, auth_headers_a):
    # 1. Create a task and two tags
    res_task = client.post(
        "/api/v1/tasks",
        json={"title": "Tag Association Task"},
        headers=auth_headers_a,
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]

    res_tag1 = client.post("/api/v1/tags", json={"name": "Tag Alpha", "color": "#10b981"}, headers=auth_headers_a)
    assert res_tag1.status_code == 201
    tag1_id = res_tag1.json()["id"]

    res_tag2 = client.post("/api/v1/tags", json={"name": "Tag Beta", "color": "#3b82f6"}, headers=auth_headers_a)
    assert res_tag2.status_code == 201
    tag2_id = res_tag2.json()["id"]

    # 2. Assign tag1 and tag2 to task
    res_assign = client.put(
        f"/api/v1/tasks/{task_id}/tags",
        json={"tag_ids": [tag1_id, tag2_id]},
        headers=auth_headers_a,
    )
    assert res_assign.status_code == 200

    # Verify TAG_ASSIGNED events in global feed
    res_feed = client.get(f"/api/v1/activity-logs?action={ActivityAction.TAG_ASSIGNED.value}", headers=auth_headers_a)
    assert res_feed.status_code == 200
    assigned_events = res_feed.json()["items"]
    assigned_entity_ids = [e["entity_id"] for e in assigned_events]
    assert tag1_id in assigned_entity_ids
    assert tag2_id in assigned_entity_ids

    # 3. Replace tags with only tag1 (removes tag2)
    res_reassign = client.put(
        f"/api/v1/tasks/{task_id}/tags",
        json={"tag_ids": [tag1_id]},
        headers=auth_headers_a,
    )
    assert res_reassign.status_code == 200

    # Verify TAG_REMOVED event for tag2
    res_removed = client.get(f"/api/v1/activity-logs?action={ActivityAction.TAG_REMOVED.value}", headers=auth_headers_a)
    assert res_removed.status_code == 200
    removed_events = res_removed.json()["items"]
    assert any(e["entity_id"] == tag2_id for e in removed_events)


def test_transaction_atomicity_and_rollback_guarantee(client, auth_headers_a, db_session, monkeypatch):
    """
    Simulate a failure during recurring series creation initial occurrence generation
    and verify the entire operation rolls back without committing partial mutations.
    """
    from app.services.recurring_task_service import RecurringTaskService
    from app.models.recurring_task import RecurringTask

    original_generate = RecurringTaskService._generate_occurrences_for_series

    def faulty_generate(self, locked_series, cutoff):
        if locked_series.title == "Atomic Rollback Series":
            raise RuntimeError("Injected database failure during occurrence generation")
        return original_generate(self, locked_series, cutoff)

    monkeypatch.setattr(RecurringTaskService, "_generate_occurrences_for_series", faulty_generate)

    # Attempt to create recurring series
    with pytest.raises(RuntimeError, match="Injected database failure"):
        client.post(
            "/api/v1/recurring-tasks",
            json={
                "title": "Atomic Rollback Series",
                "frequency": "DAILY",
                "interval": 1,
                "start_date": "2026-11-10",
            },
            headers=auth_headers_a,
        )

    # Verify atomic rollback directly against db_session: series does NOT exist
    from sqlalchemy import select
    crashed_series = db_session.execute(
        select(RecurringTask).where(RecurringTask.title == "Atomic Rollback Series")
    ).scalar_one_or_none()
    assert crashed_series is None

    # Activity log must NOT have recorded the series
    crashed_log = db_session.execute(
        select(ActivityLog).where(ActivityLog.action == ActivityAction.RECURRING_SERIES_CREATED.value)
    ).scalars().all()
    assert not any(
        (log.extra_metadata or {}).get("title") == "Atomic Rollback Series"
        for log in crashed_log
    )


def test_task_transaction_atomicity_failure_on_activity_log(client, auth_headers_a, db_session, monkeypatch):
    """
    Scenario A: Business mutation succeeds internally, but ActivityLogRepository.create() fails.
    -> Task mutation rolls back; no task and no activity record persist.
    """
    from app.repositories.activity_log_repository import ActivityLogRepository
    from sqlalchemy import select

    original_create = ActivityLogRepository.create

    def faulty_activity_create(self, log, commit=False):
        if log.action == ActivityAction.TASK_CREATED.value and (log.extra_metadata or {}).get("title") == "Scenario A Task":
            raise RuntimeError("Injected activity log failure on create")
        return original_create(self, log, commit)

    monkeypatch.setattr(ActivityLogRepository, "create", faulty_activity_create)

    with pytest.raises(RuntimeError, match="Injected activity log failure on create"):
        client.post(
            "/api/v1/tasks",
            json={"title": "Scenario A Task"},
            headers=auth_headers_a,
        )

    # Verify task was NOT persisted
    task_a = db_session.execute(
        select(Task).where(Task.title == "Scenario A Task")
    ).scalar_one_or_none()
    assert task_a is None

    # Verify no activity log exists
    logs_a = db_session.execute(
        select(ActivityLog).where(ActivityLog.action == ActivityAction.TASK_CREATED.value)
    ).scalars().all()
    assert not any((l.extra_metadata or {}).get("title") == "Scenario A Task" for l in logs_a)


def test_task_transaction_atomicity_failure_after_activity_flush(monkeypatch):
    """
    Scenario B: Activity record is flushed, but a subsequent step in the transaction fails.
    -> Task and activity records both roll back.
    """
    import os
    import tempfile
    from app.db.session import Base
    from app.models.user import User
    from app.models.task import Task
    from app.repositories.activity_log_repository import ActivityLogRepository
    from app.services.task_service import TaskService
    from app.schemas.task import TaskCreateRequest, TaskUpdateRequest
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    db_uri = f"sqlite:///{db_path.replace(os.sep, '/')}"
    iso_engine = create_engine(db_uri)
    Base.metadata.create_all(bind=iso_engine)
    Session = sessionmaker(bind=iso_engine)
    session = Session()

    try:
        # 1. Create a pristine test user
        user = User(
            email="task_atomicity_b@example.com",
            display_name="Atomicity User B",
            hashed_password=hash_password("PasswordB123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()

        task_service = TaskService(session)

        # 2. Create a baseline task directly via service
        created = task_service.create_task(
            user_id=user.id,
            payload=TaskCreateRequest(title="Baseline Task B"),
        )
        task_b_id = created.id

        # 3. Inject failure during activity log creation on update (after repo.update has flushed task changes)
        original_create = ActivityLogRepository.create

        def faulty_update_activity(self, log, commit=False):
            if log.action == ActivityAction.TASK_UPDATED.value and (log.extra_metadata or {}).get("title") == "Updated Title B":
                raise RuntimeError("Injected failure during task update activity")
            return original_create(self, log, commit)

        monkeypatch.setattr(ActivityLogRepository, "create", faulty_update_activity)

        # 4. Attempt update; it must raise RuntimeError and trigger self.db.rollback()
        with pytest.raises(RuntimeError, match="Injected failure during task update activity"):
            task_service.update_task(
                user_id=user.id,
                task_id=task_b_id,
                payload=TaskUpdateRequest(title="Updated Title B"),
            )

        # 5. Verify task still has original title in database (update rolled back)
        task_b = session.execute(
            select(Task).where(Task.id == task_b_id)
        ).scalar_one_or_none()
        assert task_b is not None
        assert task_b.title == "Baseline Task B"

        # Verify no TASK_UPDATED log persisted for "Updated Title B"
        update_logs = session.execute(
            select(ActivityLog).where(ActivityLog.task_id == task_b_id, ActivityLog.action == ActivityAction.TASK_UPDATED.value)
        ).scalars().all()
        assert len(update_logs) == 0
    finally:
        session.close()
        iso_engine.dispose()
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_project_transaction_atomicity_failure_on_activity_log(client, auth_headers_a, db_session, monkeypatch):
    """
    Scenario A: Project creation succeeds internally, but activity log insert fails.
    -> Project creation rolls back.
    """
    from app.repositories.activity_log_repository import ActivityLogRepository
    from app.models.project import Project
    from sqlalchemy import select

    original_create = ActivityLogRepository.create

    def faulty_create(self, log, commit=False):
        if log.action == ActivityAction.PROJECT_CREATED.value and (log.extra_metadata or {}).get("name") == "Scenario A Project":
            raise RuntimeError("Injected project activity log error")
        return original_create(self, log, commit)

    monkeypatch.setattr(ActivityLogRepository, "create", faulty_create)

    with pytest.raises(RuntimeError, match="Injected project activity log error"):
        client.post(
            "/api/v1/projects",
            json={"name": "Scenario A Project", "color": "#10b981"},
            headers=auth_headers_a,
        )

    # Verify project was not persisted
    proj_a = db_session.execute(
        select(Project).where(Project.name == "Scenario A Project")
    ).scalar_one_or_none()
    assert proj_a is None


def test_project_transaction_atomicity_failure_after_activity_flush(monkeypatch):
    """
    Scenario B: Failure during project update activity log or post-flush step.
    -> Project update rolls back to baseline name.
    """
    import os
    import tempfile
    from app.db.session import Base
    from app.models.user import User
    from app.models.project import Project
    from app.services.project_service import ProjectService
    from app.repositories.activity_log_repository import ActivityLogRepository
    from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    db_uri = f"sqlite:///{db_path.replace(os.sep, '/')}"
    iso_engine = create_engine(db_uri)
    Base.metadata.create_all(bind=iso_engine)
    Session = sessionmaker(bind=iso_engine)
    session = Session()

    try:
        # 1. Create a pristine test user
        user = User(
            email="proj_atomicity_b@example.com",
            display_name="Proj Atomicity User B",
            hashed_password=hash_password("PasswordB123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()

        project_service = ProjectService(session)

        # 2. Create baseline project
        created = project_service.create_project(
            user_id=user.id,
            payload=ProjectCreateRequest(name="Baseline Project B", color="#10b981"),
        )
        proj_b_id = created.id

        # 3. Inject failure during activity log creation on update
        original_create = ActivityLogRepository.create

        def faulty_update_activity(self, log, commit=False):
            if log.action == ActivityAction.PROJECT_UPDATED.value and (log.extra_metadata or {}).get("name") == "Mutated Name B":
                raise RuntimeError("Injected failure during project update activity")
            return original_create(self, log, commit)

        monkeypatch.setattr(ActivityLogRepository, "create", faulty_update_activity)

        with pytest.raises(RuntimeError, match="Injected failure during project update activity"):
            project_service.update_project(
                project_id=proj_b_id,
                user_id=user.id,
                payload=ProjectUpdateRequest(name="Mutated Name B"),
            )

        # 4. Verify project name remains baseline
        proj_b = session.execute(
            select(Project).where(Project.id == proj_b_id)
        ).scalar_one_or_none()
        assert proj_b is not None
        assert proj_b.name == "Baseline Project B"
    finally:
        session.close()
        iso_engine.dispose()
        try:
            os.remove(db_path)
        except OSError:
            pass

