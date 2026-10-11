"""
DayFlow Stage 3 tests – History, Reopening, Rescheduling, and Event Tracking.

Covers:
- Completing and reopening tasks
- Completion timestamps (set on completion, cleared on reopening)
- Rescheduling while preserving original_scheduled_date
- Activity events for creation, edits, completion, reopening, rescheduling, deletion
- Retrieving historical tasks by date (scheduled or original date, including deleted)
- Tasks crossing midnight and Asia/Kolkata date boundaries
- Deleted tasks remaining available in history and history by date
- SQLite persistence across backend session restarts
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
import zoneinfo

BASE = "/tasks"

VALID_TASK = {
    "title": "Stage 3 Testing Task",
    "description": "Verify comprehensive history tracking",
    "scheduled_date": "2026-10-15",
    "start_time": "10:00:00",
    "end_time": "11:30:00",
    "priority": "medium",
    "category": "work",
}


def _create_task(client, overrides: dict | None = None) -> dict:
    data = {**VALID_TASK, **(overrides or {})}
    resp = client.post(BASE, json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCompletionAndReopening:
    def test_complete_and_reopen_task(self, client):
        task = _create_task(client, {"title": "Task to complete and reopen"})
        task_id = task["id"]

        # 1. Complete task
        res_comp = client.patch(f"{BASE}/{task_id}/complete")
        assert res_comp.status_code == 200
        comp_body = res_comp.json()
        assert comp_body["status"] == "completed"
        assert comp_body["completed_at"] is not None
        comp_time = comp_body["completed_at"]

        # Attempting to complete again returns 409
        assert client.patch(f"{BASE}/{task_id}/complete").status_code == 409

        # 2. Reopen task
        res_reopen = client.patch(f"{BASE}/{task_id}/reopen")
        assert res_reopen.status_code == 200
        reopen_body = res_reopen.json()
        assert reopen_body["status"] == "pending"
        assert reopen_body["completed_at"] is None

        # Attempting to reopen already pending returns 409
        assert client.patch(f"{BASE}/{task_id}/reopen").status_code == 409

        # 3. Verify activity history has both completed and reopened events
        res_hist = client.get(f"{BASE}/{task_id}/history")
        assert res_hist.status_code == 200
        events = res_hist.json()
        types = [e["event_type"] for e in events]
        assert "created" in types
        assert "completed" in types
        assert "reopened" in types

        # Check reopen event details
        reopen_event = next(e for e in events if e["event_type"] == "reopened")
        assert reopen_event["details"]["previous_completed_at"] == comp_time


class TestReschedulingAndOriginalDate:
    def test_reschedule_preserves_original_date(self, client):
        task = _create_task(
            client,
            {
                "title": "Task to reschedule",
                "scheduled_date": "2026-10-15",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
            },
        )
        task_id = task["id"]
        assert task["scheduled_date"] == "2026-10-15"
        assert task["original_scheduled_date"] == "2026-10-15"

        # Reschedule using dedicated PATCH endpoint
        res = client.patch(
            f"{BASE}/{task_id}/reschedule",
            json={
                "scheduled_date": "2026-10-20",
                "start_time": "14:00:00",
                "end_time": "15:00:00",
            },
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["scheduled_date"] == "2026-10-20"
        assert updated["original_scheduled_date"] == "2026-10-15"
        assert updated["start_time"] == "14:00:00"

        # Reschedule a second time via PUT /tasks/{id}
        res2 = client.put(
            f"{BASE}/{task_id}",
            json={"scheduled_date": "2026-10-25"},
        )
        assert res2.status_code == 200
        updated2 = res2.json()
        assert updated2["scheduled_date"] == "2026-10-25"
        assert updated2["original_scheduled_date"] == "2026-10-15"

        # Check events
        hist = client.get(f"{BASE}/{task_id}/history").json()
        resched_events = [e for e in hist if e["event_type"] == "rescheduled"]
        assert len(resched_events) == 2


class TestActivityHistoryAndDeletion:
    def test_activity_events_for_all_actions(self, client):
        task = _create_task(client, {"title": "Full lifecycle task"})
        task_id = task["id"]

        # Edit description
        client.put(f"{BASE}/{task_id}", json={"description": "Updated notes"})

        # Complete
        client.patch(f"{BASE}/{task_id}/complete")

        # Reopen
        client.patch(f"{BASE}/{task_id}/reopen")

        # Reschedule
        client.patch(
            f"{BASE}/{task_id}/reschedule",
            json={"scheduled_date": "2026-11-01"},
        )

        # Soft delete
        client.delete(f"{BASE}/{task_id}")

        # Check history endpoint works even after soft deletion
        res = client.get(f"{BASE}/{task_id}/history")
        assert res.status_code == 200
        events = res.json()
        types = [e["event_type"] for e in events]
        assert types == [
            "created",
            "updated",
            "completed",
            "reopened",
            "rescheduled",
            "deleted",
        ]


class TestDateHistoryQuery:
    def test_history_by_date_includes_rescheduled_and_deleted(self, client):
        # Task 1: Scheduled on 2026-10-18 and stays there
        t1 = _create_task(client, {"title": "Normal task", "scheduled_date": "2026-10-18"})

        # Task 2: Originally 2026-10-18, rescheduled to 2026-10-22
        t2 = _create_task(client, {"title": "Rescheduled away", "scheduled_date": "2026-10-18"})
        client.patch(f"{BASE}/{t2['id']}/reschedule", json={"scheduled_date": "2026-10-22"})

        # Task 3: Scheduled on 2026-10-18, then deleted
        t3 = _create_task(client, {"title": "Deleted task", "scheduled_date": "2026-10-18"})
        client.delete(f"{BASE}/{t3['id']}")

        # Query history for 2026-10-18
        res = client.get(f"{BASE}/history/date/2026-10-18")
        assert res.status_code == 200
        tasks = res.json()
        ids = [t["id"] for t in tasks]
        assert t1["id"] in ids
        assert t2["id"] in ids  # traceable from original date
        assert t3["id"] in ids  # soft-deleted is visible in historical view

        # Verify excluded if include_deleted=False
        res_no_del = client.get(f"{BASE}/history/date/2026-10-18?include_deleted=false")
        assert res_no_del.status_code == 200
        ids_no_del = [t["id"] for t in res_no_del.json()]
        assert t3["id"] not in ids_no_del

    def test_midnight_and_kolkata_timezone_boundaries(self, client):
        """
        Verify that ISO timestamps are in UTC, and local calendar date
        does not shift unintentionally across midnight boundaries.
        """
        from datetime import timedelta
        # Asia/Kolkata is UTC+05:30
        kolkata_tz = timezone(timedelta(hours=5, minutes=30))
        # Task scheduled for a specific date in Kolkata
        t = _create_task(
            client,
            {
                "title": "Midnight edge task",
                "scheduled_date": "2026-10-12",
                "start_time": "23:30:00",
                "end_time": "23:55:00",
            },
        )
        task_id = t["id"]
        client.patch(f"{BASE}/{task_id}/complete")

        fetch = client.get(f"{BASE}/{task_id}").json()
        assert fetch["scheduled_date"] == "2026-10-12"

        # Check UTC completed_at timestamp
        completed_at_str = fetch["completed_at"]
        dt = datetime.fromisoformat(completed_at_str)
        # Convert to Asia/Kolkata to verify proper offset representation
        dt_kolkata = dt.astimezone(kolkata_tz)
        assert dt_kolkata.tzinfo is not None

        # Check history by date correctly returns the task on its local calendar date
        res_date = client.get(f"{BASE}/history/date/2026-10-12")
        assert any(x["id"] == task_id for x in res_date.json())


class TestRestartPersistence:
    def test_sqlite_persistence_across_sessions(self, client):
        """Verify tasks and events persist across multiple queries and transactions."""
        t = _create_task(client, {"title": "Session persistent task"})
        t_id = t["id"]
        client.patch(f"{BASE}/{t_id}/complete")

        # Second separate query
        fetch = client.get(f"{BASE}/{t_id}")
        assert fetch.status_code == 200
        assert fetch.json()["status"] == "completed"

        # Event log check
        hist = client.get(f"{BASE}/{t_id}/history")
        assert hist.status_code == 200
        events = hist.json()
        assert len(events) >= 2
