"""
DayFlow tests – Task CRUD endpoints.

Covers:
- Task creation (valid + invalid)
- Listing tasks
- Retrieving a task by ID (found + 404)
- Updating a task (partial update, invalid data)
- Completing a task (idempotency guard)
- Soft-deleting a task (task disappears from list, 404 on fetch)
- Persistence across separate DB sessions
"""
from __future__ import annotations

import pytest

BASE = "/tasks"

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

VALID_TASK = {
    "title": "Write unit tests",
    "description": "Cover all happy and error paths",
    "scheduled_date": "2026-10-15",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "priority": "high",
    "category": "work",
}


def _create_task(client, overrides: dict | None = None) -> dict:
    data = {**VALID_TASK, **(overrides or {})}
    resp = client.post(BASE, json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Creation
# --------------------------------------------------------------------------- #

class TestCreateTask:
    def test_create_valid(self, client):
        task = _create_task(client)
        assert task["id"] > 0
        assert task["title"] == VALID_TASK["title"]
        assert task["status"] == "pending"
        assert task["scheduled_date"] == "2026-10-15"
        assert task["original_scheduled_date"] == "2026-10-15"
        assert task["deleted_at"] is None

    def test_create_minimal(self, client):
        """Only required fields should succeed."""
        resp = client.post(
            BASE,
            json={"title": "Minimal task", "scheduled_date": "2026-10-16"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["priority"] == "medium"
        assert body["category"] == "other"
        assert body["start_time"] is None

    def test_create_missing_title(self, client):
        resp = client.post(BASE, json={"scheduled_date": "2026-10-16"})
        assert resp.status_code == 422

    def test_create_missing_date(self, client):
        resp = client.post(BASE, json={"title": "No date"})
        assert resp.status_code == 422

    def test_create_invalid_priority(self, client):
        resp = client.post(
            BASE, json={**VALID_TASK, "priority": "critical"}
        )
        assert resp.status_code == 422

    def test_create_invalid_time_range(self, client):
        """end_time before start_time should be rejected."""
        resp = client.post(
            BASE,
            json={**VALID_TASK, "start_time": "12:00:00", "end_time": "09:00:00"},
        )
        assert resp.status_code == 422

    def test_create_empty_title(self, client):
        resp = client.post(
            BASE, json={**VALID_TASK, "title": ""}
        )
        assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Listing
# --------------------------------------------------------------------------- #

class TestListTasks:
    def test_list_returns_tasks(self, client):
        _create_task(client, {"title": "List test A"})
        _create_task(client, {"title": "List test B"})
        resp = client.get(BASE)
        assert resp.status_code == 200
        body = resp.json()
        assert "tasks" in body
        assert "total" in body
        assert body["total"] >= 2

    def test_list_excludes_deleted(self, client):
        task = _create_task(client, {"title": "To be deleted"})
        client.delete(f"{BASE}/{task['id']}")
        resp = client.get(BASE)
        ids = [t["id"] for t in resp.json()["tasks"]]
        assert task["id"] not in ids

    def test_list_filter_by_status(self, client):
        task = _create_task(client, {"title": "Filter pending"})
        resp = client.get(BASE, params={"status": "pending"})
        assert resp.status_code == 200
        for t in resp.json()["tasks"]:
            assert t["status"] == "pending"

    def test_list_pagination(self, client):
        for i in range(5):
            _create_task(client, {"title": f"Page task {i}"})
        resp = client.get(BASE, params={"skip": 0, "limit": 2})
        assert resp.status_code == 200
        assert len(resp.json()["tasks"]) <= 2


# --------------------------------------------------------------------------- #
# Retrieve by ID
# --------------------------------------------------------------------------- #

class TestGetTask:
    def test_get_existing(self, client):
        task = _create_task(client, {"title": "Get me"})
        resp = client.get(f"{BASE}/{task['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task["id"]

    def test_get_nonexistent(self, client):
        resp = client.get(f"{BASE}/999999")
        assert resp.status_code == 404

    def test_get_deleted_returns_404(self, client):
        task = _create_task(client, {"title": "Deleted task"})
        client.delete(f"{BASE}/{task['id']}")
        resp = client.get(f"{BASE}/{task['id']}")
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #

class TestUpdateTask:
    def test_update_title(self, client):
        task = _create_task(client, {"title": "Old title"})
        resp = client.put(
            f"{BASE}/{task['id']}", json={"title": "New title"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

    def test_update_reschedule_preserves_original(self, client):
        task = _create_task(client, {"scheduled_date": "2026-10-15"})
        resp = client.put(
            f"{BASE}/{task['id']}", json={"scheduled_date": "2026-10-20"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["scheduled_date"] == "2026-10-20"
        assert body["original_scheduled_date"] == "2026-10-15"

    def test_update_invalid_time_range(self, client):
        task = _create_task(client)
        resp = client.put(
            f"{BASE}/{task['id']}",
            json={"start_time": "18:00:00", "end_time": "09:00:00"},
        )
        assert resp.status_code == 422

    def test_update_nonexistent(self, client):
        resp = client.put(f"{BASE}/999999", json={"title": "Ghost"})
        assert resp.status_code == 404

    def test_update_invalid_category(self, client):
        task = _create_task(client)
        resp = client.put(
            f"{BASE}/{task['id']}", json={"category": "hobbies"}
        )
        assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Complete
# --------------------------------------------------------------------------- #

class TestCompleteTask:
    def test_complete_pending_task(self, client):
        task = _create_task(client, {"title": "To complete"})
        resp = client.patch(f"{BASE}/{task['id']}/complete")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["completed_at"] is not None

    def test_complete_already_completed(self, client):
        task = _create_task(client, {"title": "Already done"})
        client.patch(f"{BASE}/{task['id']}/complete")
        resp = client.patch(f"{BASE}/{task['id']}/complete")
        assert resp.status_code == 409

    def test_complete_nonexistent(self, client):
        resp = client.patch(f"{BASE}/999999/complete")
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Delete (soft)
# --------------------------------------------------------------------------- #

class TestDeleteTask:
    def test_soft_delete(self, client):
        task = _create_task(client, {"title": "Delete me"})
        resp = client.delete(f"{BASE}/{task['id']}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Task deleted successfully"

    def test_delete_nonexistent(self, client):
        resp = client.delete(f"{BASE}/999999")
        assert resp.status_code == 404

    def test_delete_hides_from_list(self, client):
        task = _create_task(client, {"title": "Hide me"})
        client.delete(f"{BASE}/{task['id']}")
        resp = client.get(BASE)
        ids = [t["id"] for t in resp.json()["tasks"]]
        assert task["id"] not in ids


# --------------------------------------------------------------------------- #
# Persistence across sessions
# --------------------------------------------------------------------------- #

class TestPersistence:
    def test_data_persists_across_requests(self, client):
        """
        Create a task in one request and verify it is retrievable in
        a separate request (simulating a new session in the same test run).
        """
        task = _create_task(client, {"title": "Persistent task"})
        task_id = task["id"]

        # Second independent request
        resp = client.get(f"{BASE}/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Persistent task"
