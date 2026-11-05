import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import zoneinfo
from sqlalchemy import (
    case,
    func,
    select,
)
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.models.category import Category
from app.models.project import Project
from app.models.recurring_task import RecurrenceFrequency, RecurringTask, RecurringTaskSkip
from app.models.task import Task, TaskPriority, TaskStatus


class AnalyticsRepository:
    """Repository handling all database queries and SQL aggregations for Productivity Analytics."""

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # 1. Overview KPIs
    # ---------------------------------------------------------
    def get_overview_task_counts(self, user_id: uuid.UUID, now_utc: datetime) -> Dict[str, int]:
        """
        Calculates root task snapshot counts:
        total active root tasks, completed, pending, overdue, and cancelled.
        Excludes archived tasks and subtasks (parent_task_id IS NOT NULL).
        """
        stmt = (
            select(
                func.count(Task.id).label("total"),
                func.count(case((Task.status == TaskStatus.COMPLETED, Task.id))).label("completed"),
                func.count(
                    case((Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.id))
                ).label("pending"),
                func.count(
                    case(
                        (
                            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
                            & (Task.due_date.isnot(None))
                            & (Task.due_date < now_utc),
                            Task.id,
                        )
                    )
                ).label("overdue"),
                func.count(case((Task.status == TaskStatus.CANCELLED, Task.id))).label("cancelled"),
            )
            .where(
                Task.user_id == user_id,
                Task.is_archived.is_(False),
                Task.parent_task_id.is_(None),
            )
        )
        row = self.db.execute(stmt).one()
        return {
            "total": row.total or 0,
            "completed": row.completed or 0,
            "pending": row.pending or 0,
            "overdue": row.overdue or 0,
            "cancelled": row.cancelled or 0,
        }

    def get_period_created_tasks_count(
        self, user_id: uuid.UUID, start_utc: datetime, end_utc: datetime
    ) -> int:
        """Count root tasks created within period."""
        stmt = (
            select(func.count(Task.id))
            .where(
                Task.user_id == user_id,
                Task.parent_task_id.is_(None),
                Task.created_at >= start_utc,
                Task.created_at <= end_utc,
            )
        )
        return self.db.execute(stmt).scalar() or 0

    def get_period_completion_and_reopened_events(
        self, user_id: uuid.UUID, start_utc: datetime, end_utc: datetime
    ) -> Tuple[int, int, int]:
        """
        Determines completion and reopening event counts within a period.
        Combines ActivityLog (Stage 2E onwards) and pre-Stage 2E task.completed_at.
        Returns: (gross_completions, reopened_events, unique_tasks_completed)
        """
        # 1. Activity log events in period
        stmt_act = (
            select(
                func.count(case((ActivityLog.action == ActivityAction.TASK_COMPLETED.value, ActivityLog.id))).label("completed"),
                func.count(case((ActivityLog.action == ActivityAction.TASK_REOPENED.value, ActivityLog.id))).label("reopened"),
                func.count(
                    func.distinct(
                        case((ActivityLog.action == ActivityAction.TASK_COMPLETED.value, ActivityLog.entity_id))
                    )
                ).label("unique_completed"),
            )
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.created_at >= start_utc,
                ActivityLog.created_at <= end_utc,
            )
        )
        row_act = self.db.execute(stmt_act).one()
        act_completed = row_act.completed or 0
        act_reopened = row_act.reopened or 0
        act_unique = row_act.unique_completed or 0

        # 2. Check for pre-Stage 2E tasks completed in this window that had no ActivityLog entry
        # A task that has completed_at in this window but no activity log TASK_COMPLETED
        stmt_pre = (
            select(func.count(Task.id))
            .where(
                Task.user_id == user_id,
                Task.parent_task_id.is_(None),
                Task.completed_at >= start_utc,
                Task.completed_at <= end_utc,
                ~Task.id.in_(
                    select(ActivityLog.entity_id).where(
                        ActivityLog.user_id == user_id,
                        ActivityLog.action == ActivityAction.TASK_COMPLETED.value,
                    )
                ),
            )
        )
        pre_count = self.db.execute(stmt_pre).scalar() or 0

        gross = act_completed + pre_count
        unique = act_unique + pre_count
        return gross, act_reopened, unique

    # ---------------------------------------------------------
    # 2. Completion Episodes for Trends and Consistency
    # ---------------------------------------------------------
    def get_raw_completion_episodes(
        self, user_id: uuid.UUID, start_utc: datetime, end_utc: datetime
    ) -> List[Tuple[datetime, uuid.UUID, str]]:
        """
        Retrieves timestamped completion & reopening episodes for trend bucketing:
        Returns list of (timestamp, task_or_entity_id, action_type: 'COMPLETED' or 'REOPENED')
        """
        # A. ActivityLog events
        stmt_logs = (
            select(ActivityLog.created_at, ActivityLog.entity_id, ActivityLog.action)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.action.in_([ActivityAction.TASK_COMPLETED.value, ActivityAction.TASK_REOPENED.value]),
                ActivityLog.created_at >= start_utc,
                ActivityLog.created_at <= end_utc,
            )
            .order_by(ActivityLog.created_at.asc())
        )
        logs = self.db.execute(stmt_logs).all()

        episodes: List[Tuple[datetime, uuid.UUID, str]] = [
            (row.created_at, row.entity_id, "COMPLETED" if row.action == ActivityAction.TASK_COMPLETED.value else "REOPENED")
            for row in logs
        ]

        # B. Supplement with tasks that have completed_at in this range but no ActivityLog entry
        logged_completed_task_ids = set(
            self.db.execute(
                select(ActivityLog.entity_id).where(
                    ActivityLog.user_id == user_id,
                    ActivityLog.action == ActivityAction.TASK_COMPLETED.value,
                )
            ).scalars().all()
        )

        stmt_tasks = (
            select(Task.completed_at, Task.id)
            .where(
                Task.user_id == user_id,
                Task.parent_task_id.is_(None),
                Task.completed_at.isnot(None),
                Task.completed_at >= start_utc,
                Task.completed_at <= end_utc,
            )
        )
        for completed_at, task_id in self.db.execute(stmt_tasks).all():
            if task_id not in logged_completed_task_ids:
                episodes.append((completed_at, task_id, "COMPLETED"))

        episodes.sort(key=lambda x: x[0])
        return episodes

    def get_raw_created_tasks(
        self, user_id: uuid.UUID, start_utc: datetime, end_utc: datetime
    ) -> List[Tuple[datetime, uuid.UUID]]:
        """Fetch created_at timestamps for root tasks within window."""
        stmt = (
            select(Task.created_at, Task.id)
            .where(
                Task.user_id == user_id,
                Task.parent_task_id.is_(None),
                Task.created_at >= start_utc,
                Task.created_at <= end_utc,
            )
            .order_by(Task.created_at.asc())
        )
        return [(r.created_at, r.id) for r in self.db.execute(stmt).all()]

    # ---------------------------------------------------------
    # 3. Project Analytics
    # ---------------------------------------------------------
    def get_projects_analytics(self, user_id: uuid.UUID, now_utc: datetime) -> List[Dict[str, Any]]:
        """
        Project-wise task counts and completion rates for all active and planned projects.
        Strictly enforces user_id on both Project and Task.
        Excludes subtasks from top-level counts.
        """
        # Outer join projects to tasks
        stmt = (
            select(
                Project.id,
                Project.name,
                Project.color,
                Project.status,
                func.count(Task.id).label("total_tasks"),
                func.count(case((Task.status == TaskStatus.COMPLETED, Task.id))).label("completed_tasks"),
                func.count(
                    case((Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.id))
                ).label("pending_tasks"),
                func.count(
                    case(
                        (
                            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
                            & (Task.due_date.isnot(None))
                            & (Task.due_date < now_utc),
                            Task.id,
                        )
                    )
                ).label("overdue_tasks"),
            )
            .outerjoin(
                Task,
                (Task.project_id == Project.id)
                & (Task.user_id == user_id)
                & (Task.is_archived.is_(False))
                & (Task.parent_task_id.is_(None)),
            )
            .where(Project.user_id == user_id, Project.is_archived.is_(False))
            .group_by(Project.id, Project.name, Project.color, Project.status)
            .order_by(Project.name.asc())
        )
        rows = self.db.execute(stmt).all()
        result = []
        for r in rows:
            tot = r.total_tasks or 0
            comp = r.completed_tasks or 0
            pct = round((comp / tot * 100), 2) if tot > 0 else 0.0
            result.append({
                "project_id": r.id,
                "project_name": r.name,
                "project_color": r.color,
                "project_status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "total_tasks": tot,
                "completed_tasks": comp,
                "pending_tasks": r.pending_tasks or 0,
                "overdue_tasks": r.overdue_tasks or 0,
                "completion_percentage": pct,
            })
        return result

    # ---------------------------------------------------------
    # 4. Category Analytics
    # ---------------------------------------------------------
    def get_categories_analytics(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Category-wise task distribution and completion rates, including Uncategorized bucket.
        Excludes archived tasks and subtasks.
        """
        # 1. Categorized tasks
        stmt_cat = (
            select(
                Category.id,
                Category.name,
                Category.color,
                Category.icon,
                func.count(Task.id).label("total_tasks"),
                func.count(case((Task.status == TaskStatus.COMPLETED, Task.id))).label("completed_tasks"),
                func.count(
                    case((Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.id))
                ).label("pending_tasks"),
            )
            .outerjoin(
                Task,
                (Task.category_id == Category.id)
                & (Task.user_id == user_id)
                & (Task.is_archived.is_(False))
                & (Task.parent_task_id.is_(None)),
            )
            .where(Category.user_id == user_id)
            .group_by(Category.id, Category.name, Category.color, Category.icon)
            .order_by(Category.name.asc())
        )
        cat_rows = self.db.execute(stmt_cat).all()

        results = []
        for r in cat_rows:
            tot = r.total_tasks or 0
            comp = r.completed_tasks or 0
            rate = round((comp / tot * 100), 2) if tot > 0 else 0.0
            results.append({
                "category_id": r.id,
                "category_name": r.name,
                "category_color": r.color,
                "category_icon": r.icon,
                "total_tasks": tot,
                "completed_tasks": comp,
                "pending_tasks": r.pending_tasks or 0,
                "completion_rate": rate,
            })

        # 2. Uncategorized bucket (tasks with category_id IS NULL)
        stmt_uncat = (
            select(
                func.count(Task.id).label("total_tasks"),
                func.count(case((Task.status == TaskStatus.COMPLETED, Task.id))).label("completed_tasks"),
                func.count(
                    case((Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.id))
                ).label("pending_tasks"),
            )
            .where(
                Task.user_id == user_id,
                Task.category_id.is_(None),
                Task.is_archived.is_(False),
                Task.parent_task_id.is_(None),
            )
        )
        uncat_row = self.db.execute(stmt_uncat).one()
        uncat_tot = uncat_row.total_tasks or 0
        if uncat_tot > 0:
            uncat_comp = uncat_row.completed_tasks or 0
            rate = round((uncat_comp / uncat_tot * 100), 2) if uncat_tot > 0 else 0.0
            results.append({
                "category_id": None,
                "category_name": "Uncategorized",
                "category_color": "#94a3b8",
                "category_icon": None,
                "total_tasks": uncat_tot,
                "completed_tasks": uncat_comp,
                "pending_tasks": uncat_row.pending_tasks or 0,
                "completion_rate": rate,
            })

        return results

    # ---------------------------------------------------------
    # 5. Workload Analytics
    # ---------------------------------------------------------
    def get_pending_tasks_for_workload(self, user_id: uuid.UUID) -> List[Tuple[TaskPriority, Optional[datetime]]]:
        """
        Fetches priority and due_date for all pending root tasks owned by user_id.
        """
        stmt = (
            select(Task.priority, Task.due_date)
            .where(
                Task.user_id == user_id,
                Task.is_archived.is_(False),
                Task.parent_task_id.is_(None),
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            )
        )
        return [(r.priority, r.due_date) for r in self.db.execute(stmt).all()]

    # ---------------------------------------------------------
    # 6. Recurring Task Analytics
    # ---------------------------------------------------------
    def get_recurring_analytics_data(self, user_id: uuid.UUID, today_local: date) -> Dict[str, Any]:
        """
        Gathers recurring series, occurrences, and skips for user.
        Calculates eligible due occurrences and frequency distributions.
        """
        # A. Series summary
        stmt_series = (
            select(
                func.count(RecurringTask.id).label("total_series"),
                func.count(case((RecurringTask.is_active.is_(True) & RecurringTask.is_stopped.is_(False), RecurringTask.id))).label("active_series"),
                func.coalesce(func.sum(RecurringTask.occurrences_generated), 0).label("total_generated"),
            )
            .where(RecurringTask.user_id == user_id)
        )
        row_s = self.db.execute(stmt_series).one()
        total_series = row_s.total_series or 0
        active_series = row_s.active_series or 0
        total_generated = int(row_s.total_generated or 0)
        paused_stopped = total_series - active_series

        # B. Frequency breakdown
        stmt_freq = (
            select(RecurringTask.frequency, func.count(RecurringTask.id))
            .where(RecurringTask.user_id == user_id)
            .group_by(RecurringTask.frequency)
        )
        freq_map: Dict[str, int] = {}
        for freq, cnt in self.db.execute(stmt_freq).all():
            val = freq.value if hasattr(freq, "value") else str(freq)
            freq_map[val.lower()] = cnt

        # C. Materialized occurrences status breakdown
        stmt_occ = (
            select(
                func.count(Task.id).label("total_materialized"),
                func.count(case((Task.status == TaskStatus.COMPLETED, Task.id))).label("completed"),
                func.count(
                    case(
                        (
                            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
                            & (Task.occurrence_date <= today_local),
                            Task.id,
                        )
                    )
                ).label("pending_due"),
                func.count(
                    case(
                        (
                            Task.occurrence_date > today_local,
                            Task.id,
                        )
                    )
                ).label("future_occurrences"),
            )
            .where(
                Task.user_id == user_id,
                Task.recurring_task_id.isnot(None),
            )
        )
        row_occ = self.db.execute(stmt_occ).one()
        completed_occ = row_occ.completed or 0
        pending_due = row_occ.pending_due or 0
        future_occ = row_occ.future_occurrences or 0

        # D. Skipped occurrences count (where skip_date <= today_local or total skips)
        stmt_skips = (
            select(func.count(RecurringTaskSkip.id))
            .where(
                RecurringTaskSkip.user_id == user_id,
                RecurringTaskSkip.skip_date <= today_local,
            )
        )
        skipped_due_count = self.db.execute(stmt_skips).scalar() or 0

        # Total skips regardless of date
        stmt_all_skips = (
            select(func.count(RecurringTaskSkip.id)).where(RecurringTaskSkip.user_id == user_id)
        )
        total_skips = self.db.execute(stmt_all_skips).scalar() or 0

        # Adherence calculation:
        # Eligible due occurrences denominator = completed_occ + pending_due + skipped_due_count
        eligible_due = completed_occ + pending_due + skipped_due_count
        adherence_rate = round((completed_occ / eligible_due * 100), 2) if eligible_due > 0 else 0.0

        return {
            "total_series": total_series,
            "active_series": active_series,
            "paused_or_stopped_series": paused_stopped,
            "total_generated_occurrences": total_generated,
            "completed_occurrences": completed_occ,
            "pending_due_occurrences": pending_due,
            "future_occurrences": future_occ,
            "skipped_occurrences": total_skips,
            "eligible_due_occurrences": eligible_due,
            "adherence_rate": adherence_rate,
            "frequency_breakdown": {
                "daily": freq_map.get("daily", 0),
                "weekly": freq_map.get("weekly", 0),
                "monthly": freq_map.get("monthly", 0),
                "yearly": freq_map.get("yearly", 0),
                "custom": freq_map.get("custom", 0),
            },
        }

