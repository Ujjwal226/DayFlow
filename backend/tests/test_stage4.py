"""
DayFlow Stage 4 tests – Productivity Analytics and Metrics.

Covers:
- GET /analytics basic response structure and fields
- Accurate calculation of completed, pending, and overdue tasks (delta-based)
- Daily completion percentage (today and 7-day trend)
- 7-day trend array formatting and dates
- Productivity heatmap data generation with intensity mapping
- Custom days parameter for heatmap (e.g. ?days=14)
- Category and priority breakdowns
- Proper timezone handling with Asia/Kolkata
- Exclusion of soft-deleted tasks from active counts
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

BASE_TASKS = "/tasks"
BASE_ANALYTICS = "/analytics"
KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def _get_kolkata_today():
    return datetime.now(KOLKATA_TZ).date()


def _create_task(client, overrides: dict | None = None) -> dict:
    today = _get_kolkata_today().isoformat()
    data = {
        "title": "Analytics Test Task",
        "description": "Task for testing analytics calculations",
        "scheduled_date": today,
        "priority": "medium",
        "category": "work",
    }
    if overrides:
        data.update(overrides)
    resp = client.post(BASE_TASKS, json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestAnalyticsEndpoint:
    def test_analytics_response_structure(self, client):
        resp = client.get(BASE_ANALYTICS)
        assert resp.status_code == 200
        data = resp.json()

        assert data["timezone"] == "Asia/Kolkata"
        assert "reported_at" in data
        assert "today_date" in data

        summary = data["summary"]
        assert "total" in summary
        assert "completed" in summary
        assert "pending" in summary
        assert "overdue" in summary
        assert "completion_percentage" in summary

        today = data["today"]
        assert "total" in today
        assert "completed" in today
        assert "pending" in today
        assert "completion_percentage" in today

        assert len(data["seven_day_trend"]) == 7
        assert len(data["heatmap"]) == 84
        assert len(data["category_breakdown"]) == 5
        assert len(data["priority_breakdown"]) == 3

    def test_analytics_metrics_calculation(self, client):
        base_resp = client.get(BASE_ANALYTICS).json()
        base_total = base_resp["summary"]["total"]
        base_pending = base_resp["summary"]["pending"]
        base_completed = base_resp["summary"]["completed"]
        base_overdue = base_resp["summary"]["overdue"]
        base_today_tot = base_resp["today"]["total"]
        base_today_comp = base_resp["today"]["completed"]
        base_today_pend = base_resp["today"]["pending"]

        today = _get_kolkata_today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # 1. Overdue pending task (scheduled yesterday)
        t_overdue = _create_task(client, {
            "title": "Overdue task",
            "scheduled_date": yesterday.isoformat(),
            "category": "health",
            "priority": "high",
        })

        # 2. Completed task today
        t_comp_today = _create_task(client, {
            "title": "Completed today",
            "scheduled_date": today.isoformat(),
            "category": "work",
            "priority": "high",
        })
        client.patch(f"{BASE_TASKS}/{t_comp_today['id']}/complete")

        # 3. Pending task today
        _create_task(client, {
            "title": "Pending today",
            "scheduled_date": today.isoformat(),
            "category": "learning",
            "priority": "low",
        })

        # 4. Pending task tomorrow
        _create_task(client, {
            "title": "Future task",
            "scheduled_date": tomorrow.isoformat(),
            "category": "personal",
            "priority": "medium",
        })

        resp = client.get(BASE_ANALYTICS)
        assert resp.status_code == 200
        data = resp.json()

        summary = data["summary"]
        assert summary["total"] == base_total + 4
        assert summary["completed"] == base_completed + 1
        assert summary["pending"] == base_pending + 3
        assert summary["overdue"] == base_overdue + 1

        today_m = data["today"]
        assert today_m["total"] == base_today_tot + 2
        assert today_m["completed"] == base_today_comp + 1
        assert today_m["pending"] == base_today_pend + 1

        # Check 7-day trend ends today
        trend = data["seven_day_trend"]
        assert len(trend) == 7
        assert trend[-1]["date"] == today.isoformat()
        assert trend[-1]["total"] == today_m["total"]
        assert trend[-1]["completed"] == today_m["completed"]

        # Check category breakdown totals match summary
        cat_total = sum(c["total"] for c in data["category_breakdown"])
        assert cat_total == summary["total"]

        # Check priority breakdown totals match summary
        prio_total = sum(p["total"] for p in data["priority_breakdown"])
        assert prio_total == summary["total"]

    def test_heatmap_custom_days_and_intensity(self, client):
        base_resp = client.get(f"{BASE_ANALYTICS}?days=14").json()
        base_hm_count = base_resp["heatmap"][-1]["completed_count"]

        today = _get_kolkata_today()

        # Create and complete 3 tasks today
        for i in range(3):
            t = _create_task(client, {"title": f"Heatmap task {i}", "scheduled_date": today.isoformat()})
            client.patch(f"{BASE_TASKS}/{t['id']}/complete")

        # Query custom window: 14 days
        resp = client.get(f"{BASE_ANALYTICS}?days=14")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["heatmap"]) == 14
        today_hm = data["heatmap"][-1]
        assert today_hm["date"] == today.isoformat()
        assert today_hm["completed_count"] == base_hm_count + 3
        assert today_hm["intensity"] >= 3  # 3-4 tasks has intensity 3

    def test_soft_deleted_excluded_from_active_metrics(self, client):
        base_resp = client.get(BASE_ANALYTICS).json()
        base_total = base_resp["summary"]["total"]

        today = _get_kolkata_today()

        t1 = _create_task(client, {"title": "Task to delete", "scheduled_date": today.isoformat()})
        t2 = _create_task(client, {"title": "Active task", "scheduled_date": today.isoformat()})

        # Soft delete t1
        client.delete(f"{BASE_TASKS}/{t1['id']}")

        resp = client.get(BASE_ANALYTICS)
        assert resp.status_code == 200
        data = resp.json()

        # Only t2 should count in delta
        assert data["summary"]["total"] == base_total + 1
