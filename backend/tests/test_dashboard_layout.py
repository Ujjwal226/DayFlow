import uuid
import pytest
from sqlalchemy import select

from app.core.dashboard_registry import (
    DashboardWidgetId,
    DashboardWidgetSize,
    WIDGET_METADATA,
    get_default_dashboard_widgets,
)
from app.core.security import create_access_token, hash_password
from app.models.dashboard_layout import DashboardLayout
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="layout_user_a@example.com",
        display_name="Layout User A",
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
        email="layout_user_b@example.com",
        display_name="Layout User B",
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


def test_get_dashboard_layout_default(client, user_a, auth_headers_a, db_session):
    """
    Test retrieving layout when user has no stored customized layout.
    Should return deterministic default layout and NOT create a row in the database.
    """
    # Verify no row in db initially
    existing_row = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.user_id == user_a.id)
    ).first()
    assert existing_row is None

    response = client.get("/api/v1/dashboard/layout", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()

    assert data["is_customized"] is False
    assert data["id"] is None
    assert data["user_id"] == str(user_a.id)
    assert len(data["widgets"]) == len(WIDGET_METADATA)

    # Verify widget contents match registry
    default_expected = get_default_dashboard_widgets()
    for received, expected in zip(data["widgets"], default_expected):
        assert received["widget_id"] == expected["widget_id"]
        assert received["is_visible"] == expected["is_visible"]
        assert received["order"] == expected["order"]
        assert received["size"] == expected["size"]

    # Verify STILL no row in db after GET
    row_after_get = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.user_id == user_a.id)
    ).first()
    assert row_after_get is None


def test_update_dashboard_layout_persistence(client, user_a, auth_headers_a, db_session):
    """
    Test updating dashboard layout persists customized visibility, order, and sizes.
    """
    custom_widgets = [
        {"widget_id": "welcome", "is_visible": False, "order": 9, "size": "small"},
        {"widget_id": "quick_actions", "is_visible": True, "order": 0, "size": "medium"},
        {"widget_id": "today_tasks", "is_visible": True, "order": 1, "size": "full"},
        {"widget_id": "productivity_overview", "is_visible": True, "order": 2, "size": "medium"},
        {"widget_id": "upcoming_tasks", "is_visible": False, "order": 3, "size": "small"},
        {"widget_id": "overdue_tasks", "is_visible": True, "order": 4, "size": "medium"},
        {"widget_id": "recent_activity", "is_visible": True, "order": 5, "size": "full"},
        {"widget_id": "projects_overview", "is_visible": True, "order": 6, "size": "medium"},
        {"widget_id": "productivity_trends", "is_visible": True, "order": 7, "size": "small"},
        {"widget_id": "recurring_insights", "is_visible": False, "order": 8, "size": "medium"},
    ]

    response = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": custom_widgets},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_customized"] is True
    assert data["id"] is not None
    assert data["user_id"] == str(user_a.id)
    assert len(data["widgets"]) == 10

    # Ensure returned widgets are sorted by order
    assert [w["widget_id"] for w in data["widgets"]] == [
        "quick_actions",
        "today_tasks",
        "productivity_overview",
        "upcoming_tasks",
        "overdue_tasks",
        "recent_activity",
        "projects_overview",
        "productivity_trends",
        "recurring_insights",
        "welcome",
    ]

    # Verify db record directly
    db_record = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.user_id == user_a.id)
    ).first()
    assert db_record is not None
    assert db_record.id == uuid.UUID(data["id"])

    # GET layout now returns customized
    get_res = client.get("/api/v1/dashboard/layout", headers=auth_headers_a)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["is_customized"] is True
    assert get_data["id"] == data["id"]
    assert get_data["widgets"][0]["widget_id"] == "quick_actions"
    assert get_data["widgets"][0]["size"] == "medium"
    assert get_data["widgets"][-1]["widget_id"] == "welcome"
    assert get_data["widgets"][-1]["is_visible"] is False


def test_reset_dashboard_layout(client, user_a, auth_headers_a, db_session):
    """
    Test resetting customized dashboard layout deletes the db record and returns default.
    """
    # Save a custom layout first
    custom_widgets = get_default_dashboard_widgets()
    custom_widgets[0]["is_visible"] = False
    put_res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": custom_widgets},
    )
    assert put_res.status_code == 200
    assert put_res.json()["is_customized"] is True

    # Now reset
    reset_res = client.post("/api/v1/dashboard/layout/reset", headers=auth_headers_a)
    assert reset_res.status_code == 200
    reset_data = reset_res.json()

    assert reset_data["is_customized"] is False
    assert reset_data["id"] is None
    assert reset_data["widgets"][0]["is_visible"] is True  # Welcome is back to visible default

    # Verify DB row is deleted
    db_record = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.user_id == user_a.id)
    ).first()
    assert db_record is None

    # Resetting again when already default is idempotent and safe
    reset_again_res = client.post("/api/v1/dashboard/layout/reset", headers=auth_headers_a)
    assert reset_again_res.status_code == 200
    assert reset_again_res.json()["is_customized"] is False


def test_dashboard_layout_validation(client, auth_headers_a):
    """
    Test validation errors:
    - Missing widgets
    - Duplicate widget IDs
    - Unknown widget IDs
    - Duplicate orders
    - Negative order
    - Invalid size variant
    """
    default_widgets = get_default_dashboard_widgets()

    # 1. Missing widgets (only 9 provided)
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": default_widgets[:-1]},
    )
    assert res.status_code == 422

    # 2. Duplicate widget ID
    dup_widgets = [dict(w) for w in default_widgets]
    dup_widgets[1]["widget_id"] = dup_widgets[0]["widget_id"]
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": dup_widgets},
    )
    assert res.status_code == 422

    # 3. Unknown widget ID
    unknown_widgets = [dict(w) for w in default_widgets]
    unknown_widgets[0]["widget_id"] = "nonexistent_widget"
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": unknown_widgets},
    )
    assert res.status_code == 422

    # 4. Duplicate display orders
    dup_order_widgets = [dict(w) for w in default_widgets]
    dup_order_widgets[1]["order"] = dup_order_widgets[0]["order"]
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": dup_order_widgets},
    )
    assert res.status_code == 422

    # 5. Negative order
    neg_order_widgets = [dict(w) for w in default_widgets]
    neg_order_widgets[0]["order"] = -1
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": neg_order_widgets},
    )
    assert res.status_code == 422

    # 6. Invalid size variant
    bad_size_widgets = [dict(w) for w in default_widgets]
    bad_size_widgets[0]["size"] = "extra-large"
    res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": bad_size_widgets},
    )
    assert res.status_code == 422


def test_dashboard_layout_multi_user_isolation(
    client, user_a, user_b, auth_headers_a, auth_headers_b, db_session
):
    """
    Test multi-user isolation: User A's customizations never bleed into User B's layout.
    """
    # User A customizes layout
    custom_widgets_a = [
        {"widget_id": "welcome", "is_visible": False, "order": 9, "size": "small"},
        {"widget_id": "quick_actions", "is_visible": True, "order": 0, "size": "medium"},
        {"widget_id": "today_tasks", "is_visible": True, "order": 1, "size": "full"},
        {"widget_id": "productivity_overview", "is_visible": True, "order": 2, "size": "medium"},
        {"widget_id": "upcoming_tasks", "is_visible": True, "order": 3, "size": "medium"},
        {"widget_id": "overdue_tasks", "is_visible": True, "order": 4, "size": "medium"},
        {"widget_id": "recent_activity", "is_visible": True, "order": 5, "size": "medium"},
        {"widget_id": "projects_overview", "is_visible": True, "order": 6, "size": "medium"},
        {"widget_id": "productivity_trends", "is_visible": True, "order": 7, "size": "medium"},
        {"widget_id": "recurring_insights", "is_visible": True, "order": 8, "size": "medium"},
    ]
    res_a = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": custom_widgets_a},
    )
    assert res_a.status_code == 200
    assert res_a.json()["is_customized"] is True

    # User B retrieves layout -> must still be default
    res_b = client.get("/api/v1/dashboard/layout", headers=auth_headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["is_customized"] is False
    assert data_b["user_id"] == str(user_b.id)
    assert data_b["widgets"][0]["widget_id"] == "welcome"
    assert data_b["widgets"][0]["is_visible"] is True

    # User B customizes their layout differently
    custom_widgets_b = [dict(w) for w in get_default_dashboard_widgets()]
    custom_widgets_b[0]["size"] = "small"
    res_b_put = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_b,
        json={"widgets": custom_widgets_b},
    )
    assert res_b_put.status_code == 200
    assert res_b_put.json()["widgets"][0]["size"] == "small"

    # Verify User A's layout remained unaffected
    res_a_check = client.get("/api/v1/dashboard/layout", headers=auth_headers_a)
    assert res_a_check.status_code == 200
    assert res_a_check.json()["widgets"][0]["widget_id"] == "quick_actions"
    assert res_a_check.json()["widgets"][-1]["is_visible"] is False


def test_dashboard_layout_cascade_delete(client, user_a, auth_headers_a, db_session):
    """
    Test foreign key ON DELETE CASCADE: Deleting user deletes their dashboard layout.
    """
    custom_widgets = get_default_dashboard_widgets()
    put_res = client.put(
        "/api/v1/dashboard/layout",
        headers=auth_headers_a,
        json={"widgets": custom_widgets},
    )
    assert put_res.status_code == 200
    layout_id = put_res.json()["id"]

    # Verify row exists in DB
    layout_row = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.id == uuid.UUID(layout_id))
    ).first()
    assert layout_row is not None

    # Delete User A
    user = db_session.scalars(select(User).where(User.id == user_a.id)).first()
    db_session.delete(user)
    db_session.commit()

    # Verify DashboardLayout was deleted
    layout_after = db_session.scalars(
        select(DashboardLayout).where(DashboardLayout.id == uuid.UUID(layout_id))
    ).first()
    assert layout_after is None

