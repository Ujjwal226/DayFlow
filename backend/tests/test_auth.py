from datetime import timedelta
import pytest
from app.core.security import create_access_token
from app.models.user import User


@pytest.fixture
def test_user(db_session):
    from app.core.security import hash_password
    user = User(
        email="auth_test@example.com",
        display_name="Auth User",
        hashed_password=hash_password("ValidPassword123!"),
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session):
    from app.core.security import hash_password
    user = User(
        email="inactive@example.com",
        display_name="Inactive User",
        hashed_password=hash_password("ValidPassword123!"),
        is_active=False,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# --- Registration Tests ---

def test_registration_successful(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "  NewUser@example.com  ",
            "display_name": "New User",
            "password": "SecurePassword1",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert data["display_name"] == "New User"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "hashed_password" not in data
    assert "password" not in data


def test_registration_duplicate_email(client, test_user):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "display_name": "Duplicate User",
            "password": "SecurePassword1",
        },
    )
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_registration_invalid_email(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "display_name": "Invalid Email",
            "password": "SecurePassword1",
        },
    )
    assert res.status_code == 422


def test_registration_weak_password(client):
    # Short password
    res1 = client.post(
        "/api/v1/auth/register",
        json={"email": "p1@example.com", "display_name": "P1", "password": "pass1"},
    )
    assert res1.status_code == 422

    # Password without digits
    res2 = client.post(
        "/api/v1/auth/register",
        json={"email": "p2@example.com", "display_name": "P2", "password": "passwordonly"},
    )
    assert res2.status_code == 422


# --- Login Tests ---

def test_login_successful(client, test_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "  AUTH_TEST@EXAMPLE.COM  ", "password": "ValidPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 15 * 60

    # Verify refresh token cookie is set and is HttpOnly
    assert "dayflow_refresh_token" in res.cookies
    cookie_header = res.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header


def test_login_incorrect_password(client, test_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword999!"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_unknown_email(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "ValidPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_inactive_user(client, inactive_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": inactive_user.email, "password": "ValidPassword123!"},
    )
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"]


# --- Protected Endpoints & Me Tests ---

def test_me_endpoint_success(client, test_user):
    token = create_access_token(user_id=test_user.id)
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)
    assert "hashed_password" not in data


def test_me_endpoint_unauthorized_no_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_endpoint_invalid_token(client):
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.signature"},
    )
    assert res.status_code == 401


def test_me_endpoint_expired_token(client, test_user):
    expired_token = create_access_token(
        user_id=test_user.id,
        expires_delta=timedelta(seconds=-10),
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401


def test_me_endpoint_inactive_user(client, inactive_user):
    token = create_access_token(user_id=inactive_user.id)
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# --- Refresh Token & Rotation Tests ---

def test_refresh_token_rotation_successful(client, test_user):
    # 1. Login to get cookie
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    initial_cookie = login_res.cookies["dayflow_refresh_token"]

    # 2. Refresh tokens
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": initial_cookie},
        headers={"Origin": "http://localhost:5173"},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    new_cookie = refresh_res.cookies["dayflow_refresh_token"]
    assert new_cookie != initial_cookie

    # 3. Attempt to use old rotated refresh token (Must trigger reuse detection!)
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": initial_cookie},
        headers={"Origin": "http://localhost:5173"},
    )
    assert reuse_res.status_code == 401
    assert "Invalid refresh token session" in reuse_res.json()["detail"]

    # 4. Now the new_cookie should ALSO be revoked because its family was revoked
    second_reuse_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": new_cookie},
        headers={"Origin": "http://localhost:5173"},
    )
    assert second_reuse_res.status_code == 401


def test_refresh_token_missing_cookie(client):
    res = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )
    assert res.status_code == 401
    assert "Refresh token missing" in res.json()["detail"]


def test_refresh_token_csrf_origin_check(client):
    res = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": "some-token"},
        headers={"Origin": "http://malicious-website.com"},
    )
    assert res.status_code == 403
    assert "CSRF" in res.json()["detail"] or "Origin not allowed" in res.json()["detail"]


# --- Logout Tests ---

def test_logout_successful(client, test_user):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    cookie_val = login_res.cookies["dayflow_refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        cookies={"dayflow_refresh_token": cookie_val},
        headers={"Origin": "http://localhost:5173"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "ok"

    # Token should no longer be usable
    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": cookie_val},
        headers={"Origin": "http://localhost:5173"},
    )
    assert refresh_after_logout.status_code == 401


def test_logout_repeated_or_empty_cookie(client):
    res = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_logout_all(client, test_user):
    # Create two login sessions
    login1 = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    cookie1 = login1.cookies["dayflow_refresh_token"]

    login2 = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "ValidPassword123!"},
    )
    cookie2 = login2.cookies["dayflow_refresh_token"]
    access_token2 = login2.json()["access_token"]

    # Call logout-all with token2
    logout_all_res = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token2}"},
    )
    assert logout_all_res.status_code == 200
    assert "Successfully revoked" in logout_all_res.json()["message"]

    # Both sessions should now fail on refresh
    res1 = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": cookie1},
        headers={"Origin": "http://localhost:5173"},
    )
    assert res1.status_code == 401

    res2 = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": cookie2},
        headers={"Origin": "http://localhost:5173"},
    )
    assert res2.status_code == 401

