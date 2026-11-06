import enum
from typing import List, Dict, Any


class DashboardWidgetId(str, enum.Enum):
    WELCOME = "welcome"
    TODAY_TASKS = "today_tasks"
    UPCOMING_TASKS = "upcoming_tasks"
    OVERDUE_TASKS = "overdue_tasks"
    PRODUCTIVITY_OVERVIEW = "productivity_overview"
    RECENT_ACTIVITY = "recent_activity"
    PROJECTS_OVERVIEW = "projects_overview"
    PRODUCTIVITY_TRENDS = "productivity_trends"
    RECURRING_INSIGHTS = "recurring_insights"
    QUICK_ACTIONS = "quick_actions"


class DashboardWidgetSize(str, enum.Enum):
    SMALL = "small"
    MEDIUM = "medium"
    FULL = "full"


WIDGET_METADATA: Dict[DashboardWidgetId, Dict[str, Any]] = {
    DashboardWidgetId.WELCOME: {
        "display_name": "Welcome & Profile",
        "default_size": DashboardWidgetSize.FULL,
        "default_order": 0,
        "default_visible": True,
    },
    DashboardWidgetId.PRODUCTIVITY_OVERVIEW: {
        "display_name": "Productivity Overview",
        "default_size": DashboardWidgetSize.FULL,
        "default_order": 1,
        "default_visible": True,
    },
    DashboardWidgetId.TODAY_TASKS: {
        "display_name": "Today's Tasks",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 2,
        "default_visible": True,
    },
    DashboardWidgetId.UPCOMING_TASKS: {
        "display_name": "Upcoming Tasks",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 3,
        "default_visible": True,
    },
    DashboardWidgetId.OVERDUE_TASKS: {
        "display_name": "Overdue Tasks",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 4,
        "default_visible": True,
    },
    DashboardWidgetId.RECENT_ACTIVITY: {
        "display_name": "Recent Activity",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 5,
        "default_visible": True,
    },
    DashboardWidgetId.PROJECTS_OVERVIEW: {
        "display_name": "Projects Overview",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 6,
        "default_visible": True,
    },
    DashboardWidgetId.PRODUCTIVITY_TRENDS: {
        "display_name": "Productivity Trends",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 7,
        "default_visible": True,
    },
    DashboardWidgetId.RECURRING_INSIGHTS: {
        "display_name": "Recurring Tasks",
        "default_size": DashboardWidgetSize.MEDIUM,
        "default_order": 8,
        "default_visible": True,
    },
    DashboardWidgetId.QUICK_ACTIONS: {
        "display_name": "Quick Actions",
        "default_size": DashboardWidgetSize.FULL,
        "default_order": 9,
        "default_visible": True,
    },
}


def get_default_dashboard_widgets() -> List[Dict[str, Any]]:
    """
    Returns the centralized deterministic default dashboard widget layout.
    All 10 supported widgets are visible with distinct order values.
    """
    sorted_items = sorted(WIDGET_METADATA.items(), key=lambda item: item[1]["default_order"])
    return [
        {
            "widget_id": widget_id.value,
            "is_visible": meta["default_visible"],
            "order": meta["default_order"],
            "size": meta["default_size"].value,
        }
        for widget_id, meta in sorted_items
    ]

