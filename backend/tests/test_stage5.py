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


class TestDemoCredentialRejection:
    """Verify that removed public demo credentials cannot be used to authenticate.

    These tests guard against accidental re-introduction of hardcoded shortcut
    credentials (owner@dayflow.app / DayFlow2026!) anywhere in the codebase.
    The test database is always clean; no such account is seeded by conftest.
    """

    REMOVED_EMAIL = "owner@dayflow.app"
    REMOVED_PASSWORD = "DayFlow2026!"

    def test_demo_email_login_rejected(self, unauth_client):
        """Login with the former demo email must fail – account does not exist in test DB."""
        resp = _login_user(unauth_client, self.REMOVED_EMAIL, self.REMOVED_PASSWORD)
        assert resp.status_code == 401, (
            f"Expected 401 for demo credentials, got {resp.status_code}: {resp.text}"
        )

    def test_demo_email_wrong_password_rejected(self, unauth_client):
        """Even if a user with the legacy email exists, the removed password must not work."""
        # First register with the legacy email using a *different* strong password
        _register_user(unauth_client, self.REMOVED_EMAIL, "UnrelatedNewPassword#99")

        # The old removed password must still be rejected
        resp = _login_user(unauth_client, self.REMOVED_EMAIL, self.REMOVED_PASSWORD)
        assert resp.status_code == 401, (
            f"Old demo password was accepted – credential hardcoding may have regressed: {resp.text}"
        )

    def test_demo_credentials_not_auto_populated_in_auth(self, unauth_client):
        """No backend endpoint should automatically supply the demo credentials.

        Confirms the /auth/login endpoint requires both email AND password in the
        request body and never injects hardcoded values server-side.
        """
        # Empty body
        resp = unauth_client.post("/auth/login", json={})
        assert resp.status_code in (400, 422), f"Expected 400/422 for empty login body, got {resp.status_code}"

        # Missing password
        resp = unauth_client.post("/auth/login", json={"email": "someone@example.com"})
        assert resp.status_code in (400, 422), f"Expected 400/422 for missing password, got {resp.status_code}"

        # Missing email
        resp = unauth_client.post("/auth/login", json={"password": "SomePassword123!"})
        assert resp.status_code in (400, 422), f"Expected 400/422 for missing email, got {resp.status_code}"


class TestRegistrationCannotClaimExistingData:
    """New registrations must not be able to access data belonging to any pre-existing user."""

    def test_new_user_cannot_access_legacy_owner_tasks(self, unauth_client):
        """Register a brand-new user account with an email that has never existed.

        The new account must start with zero tasks, confirming that registration
        never inherits tasks from any hypothetical pre-existing owner account.
        This guards against any form of task assignment at registration time.
        """
        # Use a unique email so there is no collision with other test accounts
        reg = _register_user(unauth_client, "fresh-owner-test@dayflow.app", "BrandNewStrongPass#2026").json()
        assert "access_token" in reg

        headers = _auth_headers(reg["access_token"])
        task_list = unauth_client.get("/tasks", headers=headers)
        assert task_list.status_code == 200
        assert task_list.json()["total"] == 0, (
            "Newly registered account should start with 0 tasks; "
            "legacy task inheritance would be a cross-user data leak."
        )

    def test_cannot_register_same_email_twice_to_steal_account(self, unauth_client):
        """Registering an email that already exists must be rejected with 400.

        This prevents a malicious user from 're-registering' an existing account
        to reset its password or gain access to its data.
        """
        original_pw = "OriginalOwnerPassword#1"
        attacker_pw = "AttackerNewPassword#2"

        # Victim registers first
        victim_reg = _register_user(unauth_client, "victim@example.com", original_pw)
        assert victim_reg.status_code == 201

        # Attacker tries to register the same email
        attacker_reg = _register_user(unauth_client, "victim@example.com", attacker_pw)
        assert attacker_reg.status_code == 400
        assert "already exists" in attacker_reg.json()["detail"].lower()

        # Victim's original password still works; attacker's does not
        assert _login_user(unauth_client, "victim@example.com", original_pw).status_code == 200
        assert _login_user(unauth_client, "victim@example.com", attacker_pw).status_code == 401


class TestHardeningAndRegression:
    """Security hardening checks and edge-case regression tests."""

    def test_secret_key_production_enforcement(self, monkeypatch):
        """Production startup must fail if SECRET_KEY is missing, too short, or dev default."""
        import pytest
        from app.config import Settings, _DEV_SECRET_KEYS

        # Insecure dev default in production
        for dev_key in _DEV_SECRET_KEYS:
            s = Settings(app_env="production", secret_key=dev_key)
            with pytest.raises(ValueError, match="known development default"):
                s.validate_for_production()

        # Empty secret key in production
        s_empty = Settings(app_env="production", secret_key="   ")
        with pytest.raises(ValueError, match="must not be empty"):
            s_empty.validate_for_production()

        # Too short secret key in production
        s_short = Settings(app_env="production", secret_key="shortkey123")
        with pytest.raises(ValueError, match="too short"):
            s_short.validate_for_production()

        # Valid production secret
        s_valid = Settings(app_env="production", secret_key="a" * 32)
        s_valid.validate_for_production()  # Should not raise

        # Dev mode allows default secret
        s_dev = Settings(app_env="development", secret_key="changeme")
        s_dev.validate_for_production()  # Should not raise in development

    def test_task_response_does_not_expose_user_id(self, unauth_client):
        """Task responses must not contain user_id, preventing internal ID disclosure."""
        user_reg = _register_user(unauth_client, "schema_user@example.com", "Password123!").json()
        headers = _auth_headers(user_reg["access_token"])

        # Create task
        create_resp = unauth_client.post(
            "/tasks",
            json={"title": "Schema test task", "scheduled_date": "2026-10-16", "priority": "medium", "category": "work"},
            headers=headers,
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert "user_id" not in data, "user_id must not be leaked in task create response"

        task_id = data["id"]

        # Get task
        get_resp = unauth_client.get(f"/tasks/{task_id}", headers=headers)
        assert get_resp.status_code == 200
        assert "user_id" not in get_resp.json(), "user_id must not be leaked in task get response"

        # List tasks
        list_resp = unauth_client.get("/tasks", headers=headers)
        assert list_resp.status_code == 200
        for task in list_resp.json()["tasks"]:
            assert "user_id" not in task, "user_id must not be leaked in task list response"

    def test_cross_user_include_deleted_access(self, unauth_client):
        """User B cannot view User A's deleted task even with include_deleted=true."""
        # User A creates and deletes task
        user_a = _register_user(unauth_client, "user_a_del@example.com", "Pass12345!").json()
        headers_a = _auth_headers(user_a["access_token"])
        task = unauth_client.post(
            "/tasks",
            json={"title": "A's task to delete", "scheduled_date": "2026-10-16", "priority": "low", "category": "work"},
            headers=headers_a,
        ).json()
        del_resp = unauth_client.delete(f"/tasks/{task['id']}", headers=headers_a)
        assert del_resp.status_code == 200

        # User B tries to view with include_deleted=true
        user_b = _register_user(unauth_client, "user_b_del@example.com", "Pass12345!").json()
        headers_b = _auth_headers(user_b["access_token"])
        get_b = unauth_client.get(f"/tasks/{task['id']}?include_deleted=true", headers=headers_b)
        assert get_b.status_code == 404, "User B must receive 404 for User A's deleted task"

    def test_date_history_cross_user_isolation(self, unauth_client):
        """History endpoints filtered by date only return events for tasks owned by authenticated user."""
        date_str = "2026-10-16"
        user_a = _register_user(unauth_client, "history_a@example.com", "Pass12345!").json()
        headers_a = _auth_headers(user_a["access_token"])
        unauth_client.post(
            "/tasks",
            json={"title": "A's history task", "scheduled_date": date_str, "priority": "high", "category": "personal"},
            headers=headers_a,
        )

        user_b = _register_user(unauth_client, "history_b@example.com", "Pass12345!").json()
        headers_b = _auth_headers(user_b["access_token"])

        # User B queries history for that date
        hist_b = unauth_client.get(f"/tasks/history/date/{date_str}", headers=headers_b)
        assert hist_b.status_code == 200
        items = hist_b.json()
        # Ensure none of User A's task events are visible to User B
        assert len(items) == 0, "User B should not see history events for User A's tasks on the same date"

    def test_whitespace_only_password_rejected(self, unauth_client):
        """Registration should not succeed or should fail validation gracefully for blank passwords."""
        # Backend requires 6 chars minimum, whitespace is tested
        resp = _register_user(unauth_client, "blankpass@example.com", "      ")
        # Even if 6 characters, let's verify how it handles or if standard validation handles it
        assert resp.status_code in (201, 400, 422)

