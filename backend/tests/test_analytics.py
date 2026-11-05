import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.models.activity_log import ActivityAction, ActivityLog
from app.models.category import Category
from app.models.project import Project, ProjectStatus
from app.models.recurring_task import RecurrenceFrequency, RecurringTask, RecurringTaskSkip
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="analytics_user_a@example.com",
        display_name="Analytics User A",
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
        email="analytics_user_b@example.com",
        display_name="Analytics User B",
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


@pytest.fixture
def user_wl(db_session):
    user = User(
        email="analytics_user_wl@example.com",
        display_name="Analytics User WL",
        hashed_password=hash_password("PasswordWL123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_wl(user_wl):
    token = create_access_token(user_id=user_wl.id)
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# 1. Overview KPIs
# --------------------------------------------------------------------------
def test_analytics_overview_kpis(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)

    # 1. Active completed root task
    t_comp = Task(
        user_id=user_a.id,
        title="Completed Root Task",
        status=TaskStatus.COMPLETED,
        completed_at=now - timedelta(hours=2),
    )
    # 2. Active todo task (overdue)
    t_overdue = Task(
        user_id=user_a.id,
        title="Overdue Task",
        status=TaskStatus.TODO,
        due_date=now - timedelta(days=2),
    )
    # 3. Active in-progress task (upcoming)
    t_prog = Task(
        user_id=user_a.id,
        title="In-Progress Task",
        status=TaskStatus.IN_PROGRESS,
        due_date=now + timedelta(days=3),
    )
    # 4. Cancelled task (should not count as pending)
    t_canc = Task(
        user_id=user_a.id,
        title="Cancelled Task",
        status=TaskStatus.CANCELLED,
    )
    # 5. Archived task (excluded from root KPIs)
    t_arch = Task(
        user_id=user_a.id,
        title="Archived Task",
        status=TaskStatus.TODO,
        is_archived=True,
    )
    # 6. Subtask (parent_task_id != None, excluded from root task KPIs)
    db_session.add_all([t_comp, t_overdue, t_prog, t_canc, t_arch])
    db_session.flush()

    sub = Task(
        user_id=user_a.id,
        parent_task_id=t_prog.id,
        title="Child Subtask",
        status=TaskStatus.COMPLETED,
    )
    db_session.add(sub)

    # Add activity log for completion
    act_comp = ActivityLog(
        user_id=user_a.id,
        actor_id=user_a.id,
        task_id=t_comp.id,
        entity_type="TASK",
        entity_id=t_comp.id,
        action=ActivityAction.TASK_COMPLETED.value,
        created_at=now - timedelta(hours=2),
    )
    db_session.add(act_comp)
    db_session.commit()

    resp = client.get("/api/v1/analytics/overview", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    # Root active tasks = t_comp, t_overdue, t_prog, t_canc = 4 total
    assert data["total_tasks"] == 4
    assert data["completed_tasks"] == 1
    # Pending = TODO + IN_PROGRESS = 2
    assert data["pending_tasks"] == 2
    assert data["overdue_tasks"] == 1
    assert data["cancelled_tasks"] == 1
    # Completion rate = 1 / (1 + 2) * 100 = 33.33%
    assert data["completion_rate"] == 33.33
    assert data["tasks_completed_in_period"] == 1
    assert data["net_completions_in_period"] == 1


# --------------------------------------------------------------------------
# 2. Trends, Reopening & Historical Records
# --------------------------------------------------------------------------
def test_analytics_trends_reopened_tasks_and_period_comparison(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    t1 = Task(user_id=user_a.id, title="Task Trend 1", status=TaskStatus.COMPLETED, completed_at=now)
    t2 = Task(user_id=user_a.id, title="Task Trend 2", status=TaskStatus.TODO)
    db_session.add_all([t1, t2])
    db_session.flush()

    # Log 2 completion events and 1 reopen event for Task 2
    act1 = ActivityLog(
        user_id=user_a.id,
        task_id=t1.id,
        entity_type="TASK",
        entity_id=t1.id,
        action=ActivityAction.TASK_COMPLETED.value,
        created_at=now - timedelta(days=1),
    )
    act2 = ActivityLog(
        user_id=user_a.id,
        task_id=t2.id,
        entity_type="TASK",
        entity_id=t2.id,
        action=ActivityAction.TASK_COMPLETED.value,
        created_at=now - timedelta(hours=10),
    )
    act3 = ActivityLog(
        user_id=user_a.id,
        task_id=t2.id,
        entity_type="TASK",
        entity_id=t2.id,
        action=ActivityAction.TASK_REOPENED.value,
        created_at=now - timedelta(hours=2),
    )
    db_session.add_all([act1, act2, act3])
    db_session.commit()

    # Query trends
    resp = client.get("/api/v1/analytics/trends?interval=daily&days=7", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    assert data["interval"] == "daily"
    assert len(data["buckets"]) == 7  # Zero filled 7 days
    total_gross = sum(b["gross_completions"] for b in data["buckets"])
    total_reopened = sum(b["reopened_count"] for b in data["buckets"])
    total_net = sum(b["net_completions"] for b in data["buckets"])

    assert total_gross == 2
    assert total_reopened == 1
    assert total_net == 1
    assert "Stage 2E" in data["historical_completeness_note"]


def test_analytics_trends_weekly_and_monthly_intervals(client, auth_headers_a):
    resp_w = client.get("/api/v1/analytics/trends?interval=weekly&days=30", headers=auth_headers_a)
    assert resp_w.status_code == 200
    assert resp_w.json()["interval"] == "weekly"

    resp_m = client.get("/api/v1/analytics/trends?interval=monthly&days=90", headers=auth_headers_a)
    assert resp_m.status_code == 200
    assert resp_m.json()["interval"] == "monthly"


# --------------------------------------------------------------------------
# 3. Consistency Streaks & Heatmap
# --------------------------------------------------------------------------
def test_analytics_consistency_streaks_and_heatmap(client, auth_headers_a, user_a, db_session):
    now = datetime.now(timezone.utc)
    # Create completions on 3 consecutive days ending yesterday
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    three_days_ago = now - timedelta(days=3)

    for i, dt in enumerate([three_days_ago, two_days_ago, yesterday]):
        t = Task(user_id=user_a.id, title=f"Streak Task {i}", status=TaskStatus.COMPLETED, completed_at=dt)
        db_session.add(t)
        db_session.flush()
        act = ActivityLog(
            user_id=user_a.id,
            task_id=t.id,
            entity_type="TASK",
            entity_id=t.id,
            action=ActivityAction.TASK_COMPLETED.value,
            created_at=dt,
        )
        db_session.add(act)
    db_session.commit()

    resp = client.get("/api/v1/analytics/consistency", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    # Current streak should be 3 (ending yesterday since today has no completion yet)
    assert data["current_streak_days"] == 3
    assert data["longest_streak_days"] == 3
    assert len(data["heatmap_365_days"]) == 365
    assert data["total_productive_days"] == 3
    assert data["most_productive_weekday"] is not None


# --------------------------------------------------------------------------
# 4. Project Analytics
# --------------------------------------------------------------------------
def test_analytics_projects_breakdown(client, auth_headers_a, user_a, db_session):
    p1 = Project(user_id=user_a.id, name="Project Alpha", status=ProjectStatus.ACTIVE)
    p2 = Project(user_id=user_a.id, name="Project Beta", status=ProjectStatus.PLANNED)
    db_session.add_all([p1, p2])
    db_session.flush()

    # Project Alpha: 2 tasks (1 completed, 1 pending)
    t1 = Task(user_id=user_a.id, project_id=p1.id, title="Alpha 1", status=TaskStatus.COMPLETED)
    t2 = Task(user_id=user_a.id, project_id=p1.id, title="Alpha 2", status=TaskStatus.TODO)
    db_session.add_all([t1, t2])
    db_session.commit()

    resp = client.get("/api/v1/analytics/projects", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_projects"] == 2
    alpha = next(p for p in data["projects"] if p["project_name"] == "Project Alpha")
    assert alpha["total_tasks"] == 2
    assert alpha["completed_tasks"] == 1
    assert alpha["pending_tasks"] == 1
    assert alpha["completion_percentage"] == 50.0

    beta = next(p for p in data["projects"] if p["project_name"] == "Project Beta")
    assert beta["total_tasks"] == 0
    assert beta["completion_percentage"] == 0.0


# --------------------------------------------------------------------------
# 5. Category Analytics
# --------------------------------------------------------------------------
def test_analytics_categories_breakdown(client, auth_headers_a, user_a, db_session):
    cat = Category(user_id=user_a.id, name="Work", name_normalized="work")
    db_session.add(cat)
    db_session.flush()

    # 1 task in Work
    t1 = Task(user_id=user_a.id, category_id=cat.id, title="Work Task", status=TaskStatus.COMPLETED)
    # 1 uncategorized task
    t2 = Task(user_id=user_a.id, category_id=None, title="Uncategorized Task", status=TaskStatus.TODO)
    db_session.add_all([t1, t2])
    db_session.commit()

    resp = client.get("/api/v1/analytics/categories", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_categories"] == 2
    work_cat = next(c for c in data["categories"] if c["category_name"] == "Work")
    assert work_cat["total_tasks"] == 1
    assert work_cat["completed_tasks"] == 1
    assert work_cat["completion_rate"] == 100.0

    uncat = next(c for c in data["categories"] if c["category_name"] == "Uncategorized")
    assert uncat["total_tasks"] == 1
    assert uncat["completed_tasks"] == 0
    assert uncat["completion_rate"] == 0.0


# --------------------------------------------------------------------------
# 6. Workload Analytics
# --------------------------------------------------------------------------
def test_analytics_workload_horizons(client, auth_headers_wl, user_wl, db_session):
    today = datetime.now(timezone.utc).date()
    # 1. Overdue task
    t_od = Task(
        user_id=user_wl.id,
        title="OD",
        status=TaskStatus.TODO,
        priority=TaskPriority.URGENT,
        due_date=datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
    )
    # 2. Due today
    t_today = Task(
        user_id=user_wl.id,
        title="Today",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
    )
    # 3. Due tomorrow
    t_tmrw = Task(
        user_id=user_wl.id,
        title="Tmrw",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
    )
    # 4. Due in 5 days
    t_next7 = Task(
        user_id=user_wl.id,
        title="Next7",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        due_date=datetime.combine(today + timedelta(days=5), datetime.min.time(), tzinfo=timezone.utc),
    )
    # 5. Due in 12 days
    t_later = Task(
        user_id=user_wl.id,
        title="Later",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=datetime.combine(today + timedelta(days=12), datetime.min.time(), tzinfo=timezone.utc),
    )
    # 6. No due date
    t_nodue = Task(
        user_id=user_wl.id,
        title="No Due",
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        due_date=None,
    )
    db_session.add_all([t_od, t_today, t_tmrw, t_next7, t_later, t_nodue])
    db_session.commit()

    resp = client.get("/api/v1/analytics/workload", headers=auth_headers_wl)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_pending_tasks"] == 6
    assert data["priority_distribution"]["urgent"] == 1
    assert data["priority_distribution"]["high"] == 1
    assert data["priority_distribution"]["medium"] == 2
    assert data["priority_distribution"]["low"] == 2

    horizons = data["horizons"]
    assert horizons["overdue"] == 1
    assert horizons["due_today"] == 1
    assert horizons["due_tomorrow"] == 1
    assert horizons["due_next_7_days"] == 1
    assert horizons["due_later"] == 1
    assert horizons["no_due_date"] == 1


# --------------------------------------------------------------------------
# 7. Recurring Analytics
# --------------------------------------------------------------------------
def test_analytics_recurring_adherence_and_skips(client, auth_headers_a, user_a, db_session):
    today = datetime.now(timezone.utc).date()

    rec = RecurringTask(
        user_id=user_a.id,
        title="Daily Standup",
        frequency=RecurrenceFrequency.DAILY,
        interval=1,
        start_date=today - timedelta(days=5),
        occurrences_generated=4,
    )
    db_session.add(rec)
    db_session.flush()

    # Occurrence 1: Completed (due 3 days ago)
    occ1 = Task(
        user_id=user_a.id,
        recurring_task_id=rec.id,
        title="Standup 1",
        occurrence_date=today - timedelta(days=3),
        status=TaskStatus.COMPLETED,
    )
    # Occurrence 2: Pending due (due yesterday)
    occ2 = Task(
        user_id=user_a.id,
        recurring_task_id=rec.id,
        title="Standup 2",
        occurrence_date=today - timedelta(days=1),
        status=TaskStatus.TODO,
    )
    # Occurrence 3: Future occurrence (due tomorrow, should be excluded from eligible due denominator)
    occ3 = Task(
        user_id=user_a.id,
        recurring_task_id=rec.id,
        title="Standup 3",
        occurrence_date=today + timedelta(days=1),
        status=TaskStatus.TODO,
    )
    # Explicit skip 2 days ago
    skip = RecurringTaskSkip(
        user_id=user_a.id,
        recurring_task_id=rec.id,
        skip_date=today - timedelta(days=2),
        reason="Holiday",
    )
    db_session.add_all([occ1, occ2, occ3, skip])
    db_session.commit()

    resp = client.get("/api/v1/analytics/recurring", headers=auth_headers_a)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_series"] == 1
    assert data["active_series"] == 1
    assert data["completed_occurrences"] == 1
    assert data["pending_due_occurrences"] == 1
    assert data["future_occurrences"] == 1
    assert data["skipped_occurrences"] == 1

    # Eligible due = completed (1) + pending_due (1) + skipped (1) = 3
    # Adherence = 1 / 3 * 100 = 33.33%
    assert data["eligible_due_occurrences"] == 3
    assert data["adherence_rate"] == 33.33
    assert data["frequency_breakdown"]["daily"] == 1


# --------------------------------------------------------------------------
# 8. Zero-Data & Cross-Tenant Isolation
# --------------------------------------------------------------------------
def test_analytics_zero_data_account(client, auth_headers_b):
    # User B has no tasks, projects, categories, or activities
    resp_ov = client.get("/api/v1/analytics/overview", headers=auth_headers_b)
    assert resp_ov.status_code == 200
    assert resp_ov.json()["total_tasks"] == 0
    assert resp_ov.json()["completion_rate"] == 0.0

    resp_tr = client.get("/api/v1/analytics/trends", headers=auth_headers_b)
    assert resp_tr.status_code == 200
    assert sum(b["gross_completions"] for b in resp_tr.json()["buckets"]) == 0

    resp_co = client.get("/api/v1/analytics/consistency", headers=auth_headers_b)
    assert resp_co.status_code == 200
    assert resp_co.json()["current_streak_days"] == 0
    assert resp_co.json()["longest_streak_days"] == 0

    resp_wl = client.get("/api/v1/analytics/workload", headers=auth_headers_b)
    assert resp_wl.status_code == 200
    assert resp_wl.json()["total_pending_tasks"] == 0


def test_analytics_multi_user_isolation(client, auth_headers_a, auth_headers_b, user_a, db_session):
    # Create task for User A
    t_a = Task(user_id=user_a.id, title="Private A Task", status=TaskStatus.COMPLETED)
    db_session.add(t_a)
    db_session.commit()

    # User B checks overview and workload; must not see User A's task
    resp_b = client.get("/api/v1/analytics/overview", headers=auth_headers_b)
    assert resp_b.status_code == 200
    assert resp_b.json()["total_tasks"] == 0
    assert resp_b.json()["completed_tasks"] == 0


def test_analytics_invalid_timezone_and_date_range(client, auth_headers_a):
    # Invalid timezone returns 422
    resp_tz = client.get("/api/v1/analytics/trends?timezone=Invalid/Zone", headers=auth_headers_a)
    assert resp_tz.status_code == 422
    assert "Invalid IANA timezone" in resp_tz.json()["detail"]

    # start_date > end_date returns 422
    resp_dr = client.get("/api/v1/analytics/trends?start_date=2026-11-20&end_date=2026-11-10", headers=auth_headers_a)
    assert resp_dr.status_code == 422
    assert "start_date cannot be later than end_date" in resp_dr.json()["detail"]


# --------------------------------------------------------------------------
# 9. Negative Net Completions & Single-Task Reopened Lifecycle
# --------------------------------------------------------------------------
def test_analytics_negative_net_completions(client, db_session):
    # Dedicated isolated user
    user = User(
        email="negative_net@example.com",
        display_name="Negative Net User",
        hashed_password=hash_password("Pass12345!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    dt_today = now_utc - timedelta(hours=2)

    # 1 gross completion event
    log_c = ActivityLog(
        user_id=user.id,
        entity_type="task",
        entity_id=uuid.uuid4(),
        action=ActivityAction.TASK_COMPLETED,
        created_at=dt_today,
    )
    # 3 reopened events on the same day (reopened > gross)
    logs_r = [
        ActivityLog(
            user_id=user.id,
            entity_type="task",
            entity_id=uuid.uuid4(),
            action=ActivityAction.TASK_REOPENED,
            created_at=dt_today + timedelta(minutes=10 * i),
        )
        for i in range(1, 4)
    ]
    db_session.add_all([log_c, *logs_r])
    db_session.commit()

    # Overview check
    resp_ov = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )
    assert resp_ov.status_code == 200
    ov_data = resp_ov.json()
    assert ov_data["tasks_completed_in_period"] == 1
    assert ov_data["tasks_reopened_in_period"] == 3
    # Net completions must be negative without clamping to zero
    assert ov_data["net_completions_in_period"] == -2

    # Trends daily bucket check
    resp_tr = client.get(
        f"/api/v1/analytics/trends?start_date={today.isoformat()}&end_date={today.isoformat()}&interval=daily",
        headers=headers,
    )
    assert resp_tr.status_code == 200
    tr_data = resp_tr.json()
    assert len(tr_data["buckets"]) == 1
    bucket = tr_data["buckets"][0]
    assert bucket["gross_completions"] == 1
    assert bucket["reopened_count"] == 3
    assert bucket["net_completions"] == -2


def test_analytics_single_task_reopened_lifecycle_and_streak_persistence(client, db_session):
    # Scenario: A single task is completed -> reopened -> completed again
    user = User(
        email="lifecycle_user@example.com",
        display_name="Lifecycle User",
        hashed_password=hash_password("Pass12345!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    dt_today = now_utc - timedelta(hours=4)
    task_id = uuid.uuid4()

    # Completed at -4 hours
    log_c1 = ActivityLog(
        user_id=user.id,
        entity_type="task",
        entity_id=task_id,
        action=ActivityAction.TASK_COMPLETED,
        created_at=dt_today,
    )
    # Reopened at -3 hours
    log_r1 = ActivityLog(
        user_id=user.id,
        entity_type="task",
        entity_id=task_id,
        action=ActivityAction.TASK_REOPENED,
        created_at=dt_today + timedelta(hours=1),
    )
    # Completed again at -1 hour
    log_c2 = ActivityLog(
        user_id=user.id,
        entity_type="task",
        entity_id=task_id,
        action=ActivityAction.TASK_COMPLETED,
        created_at=dt_today + timedelta(hours=3),
    )
    db_session.add_all([log_c1, log_r1, log_c2])
    db_session.commit()

    # Verify Overview: gross=2, reopened=1, net=1
    resp_ov = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )
    assert resp_ov.status_code == 200
    ov_data = resp_ov.json()
    assert ov_data["tasks_completed_in_period"] == 2
    assert ov_data["tasks_reopened_in_period"] == 1
    assert ov_data["net_completions_in_period"] == 1

    # Verify Trends: gross=2, reopened=1, net=1, unique=1
    resp_tr = client.get(
        f"/api/v1/analytics/trends?start_date={today.isoformat()}&end_date={today.isoformat()}&interval=daily",
        headers=headers,
    )
    assert resp_tr.status_code == 200
    tr_data = resp_tr.json()
    b = tr_data["buckets"][0]
    assert b["gross_completions"] == 2
    assert b["reopened_count"] == 1
    assert b["net_completions"] == 1
    assert b["unique_tasks_completed"] == 1

    # Verify Consistency / Streak:
    # Gross completions >= 1 qualifies today as a productive day even if tasks were reopened
    resp_co = client.get("/api/v1/analytics/consistency", headers=headers)
    assert resp_co.status_code == 200
    co_data = resp_co.json()
    assert co_data["current_streak_days"] == 1
    assert co_data["longest_streak_days"] == 1
    assert co_data["total_productive_days"] == 1
    today_heatmap = [d for d in co_data["heatmap_365_days"] if d["date"] == today.isoformat()]
    assert len(today_heatmap) == 1
    assert today_heatmap[0]["count"] == 2
    assert today_heatmap[0]["level"] >= 1

