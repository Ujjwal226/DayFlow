"""
DayFlow Stage 5 tests – Multi-User Authentication, Ownership, and Cross-User Data Isolation.

Covers:
- User registration (success, duplicate email rejection, invalid inputs)
- User login (success, incorrect password, nonexistent email)
- Session handling (GET /auth/me, POST /auth/logout)
- Enforced 401 Unauthorized across all protected endpoints when unauthenticated
- Strict cross-user data isolation:
  * Users cannot view each other's tasks in list or by ID
  * Users cannot update, reschedule, complete, reopen, or delete each other's tasks
  * Users cannot view each other's task history
  * Analytics and heatmap are strictly private and isolated per user
- Passwords securely hashed with bcrypt in the database
"""
from __future__ import annotations

import bcrypt
import pytest
from sqlalchemy import select

from app import models

BASE_AUTH = "/auth"
BASE_TASKS = "/tasks"
BASE_ANALYTICS = "/analytics"


def _register_user(client, email: str, password: str = "SecurePass123!", full_name: str = "Test User") -> dict:
    resp = client.post(
        f"{BASE_AUTH}/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    return resp


def _login_user(client, email: str, password: str = "SecurePass123!") -> dict:
    resp = client.post(
        f"{BASE_AUTH}/login",
        json={"email": email, "password": password},
    )
    return resp


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuthenticationEndpoints:
    def test_registration_success(self, unauth_client):
        resp = _register_user(unauth_client, "alice@example.com", "Password123!", "Alice Wonderland")
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["full_name"] == "Alice Wonderland"
        assert "id" in data["user"]

    def test_registration_duplicate_email(self, unauth_client):
        resp1 = _register_user(unauth_client, "dup@example.com", "Pass123!")
        assert resp1.status_code == 201

        # Attempt same email with different casing
        resp2 = _register_user(unauth_client, "DUP@example.com", "DifferentPass!")
        assert resp2.status_code == 400
        assert "already exists" in resp2.json()["detail"].lower()

    def test_registration_validation(self, unauth_client):
        # Invalid email
        resp = _register_user(unauth_client, "notanemail", "Pass123!")
        assert resp.status_code == 422

        # Too short password
        resp = _register_user(unauth_client, "short@example.com", "123")
        assert resp.status_code == 422

    def test_login_success(self, unauth_client):
        _register_user(unauth_client, "bob@example.com", "SecretPass123!")
        resp = _login_user(unauth_client, "bob@example.com", "SecretPass123!")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "bob@example.com"

    def test_login_invalid_credentials(self, unauth_client):
        _register_user(unauth_client, "charlie@example.com", "CorrectPassword123!")

        # Wrong password
        resp_wrong_pw = _login_user(unauth_client, "charlie@example.com", "WrongPassword!")
        assert resp_wrong_pw.status_code == 401
        assert "invalid email or password" in resp_wrong_pw.json()["detail"].lower()

        # Nonexistent email
        resp_no_user = _login_user(unauth_client, "ghost@example.com", "AnyPassword!")
        assert resp_no_user.status_code == 401

    def test_get_me_and_logout(self, unauth_client):
        reg = _register_user(unauth_client, "dave@example.com", "DavePass123!", "Dave").json()
        token = reg["access_token"]
        headers = _auth_headers(token)

        # GET /auth/me
        resp_me = unauth_client.get(f"{BASE_AUTH}/me", headers=headers)
        assert resp_me.status_code == 200
        assert resp_me.json()["email"] == "dave@example.com"

        # POST /auth/logout
        resp_logout = unauth_client.post(f"{BASE_AUTH}/logout", headers=headers)
        assert resp_logout.status_code == 200
        assert "logged out" in resp_logout.json()["message"].lower()

    def test_password_hashed_in_database(self, unauth_client, db_session):
        plain_pw = "PlainPasswordToHash!"
        _register_user(unauth_client, "hashcheck@example.com", plain_pw)

        user = db_session.scalars(
            select(models.User).where(models.User.email == "hashcheck@example.com")
        ).first()
        assert user is not None
        assert user.hashed_password != plain_pw
        assert user.hashed_password.startswith("$2b$")
        assert bcrypt.checkpw(plain_pw.encode("utf-8"), user.hashed_password.encode("utf-8"))


class TestUnauthorizedAccess:
    def test_endpoints_reject_unauthenticated(self, unauth_client):
        # List tasks
        assert unauth_client.get(BASE_TASKS).status_code == 401

        # Create task
        assert unauth_client.post(BASE_TASKS, json={"title": "Test", "scheduled_date": "2026-10-15"}).status_code == 401

        # Get task by ID
        assert unauth_client.get(f"{BASE_TASKS}/1").status_code == 401

        # Update task
        assert unauth_client.put(f"{BASE_TASKS}/1", json={"title": "New"}).status_code == 401

        # Complete task
        assert unauth_client.patch(f"{BASE_TASKS}/1/complete").status_code == 401

        # Reopen task
        assert unauth_client.patch(f"{BASE_TASKS}/1/reopen").status_code == 401

        # Reschedule task
        assert unauth_client.patch(f"{BASE_TASKS}/1/reschedule", json={"scheduled_date": "2026-10-16"}).status_code == 401

        # Task history
        assert unauth_client.get(f"{BASE_TASKS}/1/history").status_code == 401

        # Delete task
        assert unauth_client.delete(f"{BASE_TASKS}/1").status_code == 401

        # Analytics
        assert unauth_client.get(BASE_ANALYTICS).status_code == 401

        # Me
        assert unauth_client.get(f"{BASE_AUTH}/me").status_code == 401

    def test_invalid_bearer_token_rejected(self, unauth_client):
        bad_headers = {"Authorization": "Bearer invalid.token.value"}
        assert unauth_client.get(BASE_TASKS, headers=bad_headers).status_code == 401
        assert unauth_client.get(BASE_ANALYTICS, headers=bad_headers).status_code == 401


class TestCrossUserDataIsolation:
    def test_cross_user_tasks_isolation(self, unauth_client):
        # 1. Register User 1 and create a task
        u1_reg = _register_user(unauth_client, "user1@example.com").json()
        u1_headers = _auth_headers(u1_reg["access_token"])

        task1_resp = unauth_client.post(
            BASE_TASKS,
            json={"title": "User 1 Private Task", "scheduled_date": "2026-10-15", "category": "work", "priority": "high"},
            headers=u1_headers,
        )
        assert task1_resp.status_code == 201
        task1 = task1_resp.json()
        task1_id = task1["id"]

        # 2. Register User 2
        u2_reg = _register_user(unauth_client, "user2@example.com").json()
        u2_headers = _auth_headers(u2_reg["access_token"])

        # 3. User 2 lists tasks -> must NOT see User 1's task
        u2_list = unauth_client.get(BASE_TASKS, headers=u2_headers)
        assert u2_list.status_code == 200
        assert u2_list.json()["total"] == 0
        assert len(u2_list.json()["tasks"]) == 0

        # 4. User 2 attempts to GET User 1's task directly -> 404
        u2_get = unauth_client.get(f"{BASE_TASKS}/{task1_id}", headers=u2_headers)
        assert u2_get.status_code == 404

        # 5. User 2 attempts to UPDATE User 1's task -> 404
        u2_put = unauth_client.put(f"{BASE_TASKS}/{task1_id}", json={"title": "Hacked"}, headers=u2_headers)
        assert u2_put.status_code == 404

        # 6. User 2 attempts to COMPLETE User 1's task -> 404
        u2_complete = unauth_client.patch(f"{BASE_TASKS}/{task1_id}/complete", headers=u2_headers)
        assert u2_complete.status_code == 404

        # 7. User 2 attempts to RESCHEDULE User 1's task -> 404
        u2_reschedule = unauth_client.patch(
            f"{BASE_TASKS}/{task1_id}/reschedule",
            json={"scheduled_date": "2026-10-20"},
            headers=u2_headers,
        )
        assert u2_reschedule.status_code == 404

        # 8. User 2 attempts to view User 1's task history -> 404
        u2_history = unauth_client.get(f"{BASE_TASKS}/{task1_id}/history", headers=u2_headers)
        assert u2_history.status_code == 404

        # 9. User 2 attempts to DELETE User 1's task -> 404
        u2_delete = unauth_client.delete(f"{BASE_TASKS}/{task1_id}", headers=u2_headers)
        assert u2_delete.status_code == 404

        # 10. User 2 queries history by date -> returns empty list
        u2_date_history = unauth_client.get(f"{BASE_TASKS}/history/date/2026-10-15", headers=u2_headers)
        assert u2_date_history.status_code == 200
        assert len(u2_date_history.json()) == 0

        # 11. Confirm User 1 can still access their task intact
        u1_get = unauth_client.get(f"{BASE_TASKS}/{task1_id}", headers=u1_headers)
        assert u1_get.status_code == 200
        assert u1_get.json()["title"] == "User 1 Private Task"

    def test_cross_user_analytics_isolation(self, unauth_client):
        # User A registers, creates 2 tasks, completes 1
        ua_reg = _register_user(unauth_client, "analytica@example.com").json()
        ua_headers = _auth_headers(ua_reg["access_token"])

        t1 = unauth_client.post(
            BASE_TASKS,
            json={"title": "A Task 1", "scheduled_date": "2026-10-15"},
            headers=ua_headers,
        ).json()
        unauth_client.post(
            BASE_TASKS,
            json={"title": "A Task 2", "scheduled_date": "2026-10-15"},
            headers=ua_headers,
        )
        unauth_client.patch(f"{BASE_TASKS}/{t1['id']}/complete", headers=ua_headers)

        # User A analytics: total=2, completed=1, pending=1, completion_percentage=50.0
        ua_analytics = unauth_client.get(BASE_ANALYTICS, headers=ua_headers).json()
        assert ua_analytics["summary"]["total"] == 2
        assert ua_analytics["summary"]["completed"] == 1
        assert ua_analytics["summary"]["pending"] == 1
        assert ua_analytics["summary"]["completion_percentage"] == 50.0

        # User B registers: has 0 tasks
        ub_reg = _register_user(unauth_client, "analyticb@example.com").json()
        ub_headers = _auth_headers(ub_reg["access_token"])

        ub_analytics = unauth_client.get(BASE_ANALYTICS, headers=ub_headers).json()
        assert ub_analytics["summary"]["total"] == 0
        assert ub_analytics["summary"]["completed"] == 0
        assert ub_analytics["summary"]["pending"] == 0
        assert ub_analytics["summary"]["completion_percentage"] == 0.0
        assert all(h["completed_count"] == 0 for h in ub_analytics["heatmap"])
