import calendar
from collections import defaultdict
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import zoneinfo
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import TaskPriority
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    CategoryAnalyticsItem,
    CategoryAnalyticsResponse,
    ConsistencyAnalyticsResponse,
    HeatmapCell,
    PeriodComparison,
    ProductivityOverviewResponse,
    ProductivityTrendsResponse,
    ProjectAnalyticsItem,
    ProjectAnalyticsResponse,
    RecurringAnalyticsResponse,
    RecurringFrequencyBreakdown,
    TrendBucket,
    WorkloadAnalyticsResponse,
    WorkloadHorizonBreakdown,
    PriorityDistribution,
)


class AnalyticsService:
    """Service handling productivity analytics calculations, time-series bucketing, and streaks."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsRepository(db)

    # ---------------------------------------------------------
    # Helper: Validate and Parse Timezone
    # ---------------------------------------------------------
    @staticmethod
    def _validate_timezone(tz_name: Optional[str]) -> zoneinfo.ZoneInfo:
        """Validate and return ZoneInfo; raise HTTP 422 if invalid."""
        if not tz_name or tz_name.strip() == "":
            return zoneinfo.ZoneInfo("UTC")
        try:
            return zoneinfo.ZoneInfo(tz_name.strip())
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid IANA timezone '{tz_name}'. Example valid timezones: 'UTC', 'America/New_York', 'Asia/Kolkata'.",
            )

    # ---------------------------------------------------------
    # 1. Productivity Overview
    # ---------------------------------------------------------
    def get_overview(
        self,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30,
    ) -> ProductivityOverviewResponse:
        """
        Calculates productivity overview KPIs.
        Root tasks snapshot + period creation and completion counts.
        """
        now_utc = datetime.now(timezone.utc)
        if start_date is None or end_date is None:
            end_utc = now_utc
            start_utc = end_utc - timedelta(days=days)
        else:
            if start_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="start_date cannot be later than end_date.",
                )
            start_utc = start_date if start_date.tzinfo else start_date.replace(tzinfo=timezone.utc)
            end_utc = end_date if end_date.tzinfo else end_date.replace(tzinfo=timezone.utc)

        # Snapshot counts
        counts = self.repo.get_overview_task_counts(user_id, now_utc)
        completed = counts["completed"]
        pending = counts["pending"]
        denom = completed + pending
        completion_rate = round((completed / denom * 100), 2) if denom > 0 else 0.0

        # Period creation and completion events
        created_in_period = self.repo.get_period_created_tasks_count(user_id, start_utc, end_utc)
        gross_comp, reopened, unique_comp = self.repo.get_period_completion_and_reopened_events(
            user_id, start_utc, end_utc
        )
        net_comp = gross_comp - reopened

        return ProductivityOverviewResponse(
            total_tasks=counts["total"],
            completed_tasks=completed,
            pending_tasks=pending,
            overdue_tasks=counts["overdue"],
            cancelled_tasks=counts["cancelled"],
            completion_rate=completion_rate,
            period_start=start_utc,
            period_end=end_utc,
            tasks_created_in_period=created_in_period,
            tasks_completed_in_period=gross_comp,
            tasks_reopened_in_period=reopened,
            net_completions_in_period=net_comp,
        )

    # ---------------------------------------------------------
    # 2. Productivity Trends
    # ---------------------------------------------------------
    def get_trends(
        self,
        user_id: uuid.UUID,
        interval: str = "daily",  # daily, weekly, monthly
        days: Optional[int] = 30,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tz_name: Optional[str] = "UTC",
    ) -> ProductivityTrendsResponse:
        """
        Generates time-series buckets of completed and created tasks with period comparisons.
        Zero-fills empty buckets within the date window.
        """
        tz = self._validate_timezone(tz_name)
        now_local = datetime.now(tz)
        today_local = now_local.date()

        if interval not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="interval must be one of 'daily', 'weekly', or 'monthly'.",
            )

        if start_date is not None and end_date is not None:
            if start_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="start_date cannot be later than end_date.",
                )
            if (end_date - start_date).days > 366:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Custom date range cannot exceed 366 days.",
                )
            d_start = start_date
            d_end = end_date
        else:
            d_end = today_local
            days_span = days if days is not None else 30
            if days_span < 1 or days_span > 366:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="days must be between 1 and 366.",
                )
            d_start = d_end - timedelta(days=days_span - 1)

        # Period length in days
        period_days = (d_end - d_start).days + 1
        prior_end = d_start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=period_days - 1)

        # Convert date range boundaries to UTC datetime for database query
        dt_start_utc = datetime(d_start.year, d_start.month, d_start.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
        dt_end_utc = datetime(d_end.year, d_end.month, d_end.day, 23, 59, 59, 999999, tzinfo=tz).astimezone(timezone.utc)

        dt_prior_start_utc = datetime(prior_start.year, prior_start.month, prior_start.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
        dt_prior_end_utc = datetime(prior_end.year, prior_end.month, prior_end.day, 23, 59, 59, 999999, tzinfo=tz).astimezone(timezone.utc)

        # Fetch raw episodes in UTC
        current_episodes = self.repo.get_raw_completion_episodes(user_id, dt_start_utc, dt_end_utc)
        prior_episodes = self.repo.get_raw_completion_episodes(user_id, dt_prior_start_utc, dt_prior_end_utc)

        current_created = self.repo.get_raw_created_tasks(user_id, dt_start_utc, dt_end_utc)
        prior_created = self.repo.get_raw_created_tasks(user_id, dt_prior_start_utc, dt_prior_end_utc)

        # Aggregate current period buckets in local timezone
        # Group episodes by day in user timezone
        episodes_by_day = defaultdict(lambda: {"gross": 0, "reopened": 0, "tasks": set()})
        for dt_utc, entity_id, action in current_episodes:
            local_d = dt_utc.astimezone(tz).date()
            if action == "COMPLETED":
                episodes_by_day[local_d]["gross"] += 1
                episodes_by_day[local_d]["tasks"].add(entity_id)
            elif action == "REOPENED":
                episodes_by_day[local_d]["reopened"] += 1

        created_by_day = defaultdict(int)
        for dt_utc, _ in current_created:
            local_d = dt_utc.astimezone(tz).date()
            created_by_day[local_d] += 1

        # Build zero-filled trend buckets based on interval
        buckets: List[TrendBucket] = []
        if interval == "daily":
            curr = d_start
            while curr <= d_end:
                day_data = episodes_by_day[curr]
                c_cnt = created_by_day[curr]
                g_comp = day_data["gross"]
                reop = day_data["reopened"]
                net = g_comp - reop
                uniq = len(day_data["tasks"])
                buckets.append(
                    TrendBucket(
                        bucket_label=curr.isoformat(),
                        start_date=curr.isoformat(),
                        end_date=curr.isoformat(),
                        created_count=c_cnt,
                        gross_completions=g_comp,
                        reopened_count=reop,
                        net_completions=net,
                        unique_tasks_completed=uniq,
                    )
                )
                curr += timedelta(days=1)

        elif interval == "weekly":
            # Group by ISO week (Monday to Sunday)
            curr = d_start
            while curr <= d_end:
                # Monday of this week
                week_start = curr - timedelta(days=curr.weekday())
                week_end = week_start + timedelta(days=6)
                # Clamp to d_start and d_end for labeling if preferred, or keep natural weeks
                b_start = max(d_start, week_start)
                b_end = min(d_end, week_end)

                # Sum across days in this week slice
                w_created = 0
                w_gross = 0
                w_reop = 0
                w_tasks = set()

                sub_curr = b_start
                while sub_curr <= b_end:
                    day_data = episodes_by_day[sub_curr]
                    w_created += created_by_day[sub_curr]
                    w_gross += day_data["gross"]
                    w_reop += day_data["reopened"]
                    w_tasks.update(day_data["tasks"])
                    sub_curr += timedelta(days=1)

                iso_yr, iso_wk, _ = curr.isocalendar()
                buckets.append(
                    TrendBucket(
                        bucket_label=f"{iso_yr}-W{iso_wk:02d}",
                        start_date=b_start.isoformat(),
                        end_date=b_end.isoformat(),
                        created_count=w_created,
                        gross_completions=w_gross,
                        reopened_count=w_reop,
                        net_completions=w_gross - w_reop,
                        unique_tasks_completed=len(w_tasks),
                    )
                )
                curr = week_end + timedelta(days=1)

        elif interval == "monthly":
            # Group by calendar month
            curr = d_start
            while curr <= d_end:
                # Month boundaries
                m_start = date(curr.year, curr.month, 1)
                last_day = calendar.monthrange(curr.year, curr.month)[1]
                m_end = date(curr.year, curr.month, last_day)

                b_start = max(d_start, m_start)
                b_end = min(d_end, m_end)

                m_created = 0
                m_gross = 0
                m_reop = 0
                m_tasks = set()

                sub_curr = b_start
                while sub_curr <= b_end:
                    day_data = episodes_by_day[sub_curr]
                    m_created += created_by_day[sub_curr]
                    m_gross += day_data["gross"]
                    m_reop += day_data["reopened"]
                    m_tasks.update(day_data["tasks"])
                    sub_curr += timedelta(days=1)

                buckets.append(
                    TrendBucket(
                        bucket_label=curr.strftime("%Y-%m"),
                        start_date=b_start.isoformat(),
                        end_date=b_end.isoformat(),
                        created_count=m_created,
                        gross_completions=m_gross,
                        reopened_count=m_reop,
                        net_completions=m_gross - m_reop,
                        unique_tasks_completed=len(m_tasks),
                    )
                )
                # Advance to next month
                if curr.month == 12:
                    curr = date(curr.year + 1, 1, 1)
                else:
                    curr = date(curr.year, curr.month + 1, 1)

        # Calculate Period Comparison
        curr_comp_total = sum(b.gross_completions for b in buckets)
        curr_created_total = sum(b.created_count for b in buckets)

        prior_comp_total = sum(1 for _, _, a in prior_episodes if a == "COMPLETED")
        prior_created_total = len(prior_created)

        comp_change = None
        if prior_comp_total > 0:
            comp_change = round(((curr_comp_total - prior_comp_total) / prior_comp_total * 100), 2)
        elif curr_comp_total > 0:
            comp_change = 100.0

        created_change = None
        if prior_created_total > 0:
            created_change = round(((curr_created_total - prior_created_total) / prior_created_total * 100), 2)
        elif curr_created_total > 0:
            created_change = 100.0

        comparison = PeriodComparison(
            current_period_completions=curr_comp_total,
            prior_period_completions=prior_comp_total,
            completion_change_percentage=comp_change,
            current_period_created=curr_created_total,
            prior_period_created=prior_created_total,
            created_change_percentage=created_change,
        )

        return ProductivityTrendsResponse(
            interval=interval,
            timezone=tz_name or "UTC",
            period_start=d_start.isoformat(),
            period_end=d_end.isoformat(),
            buckets=buckets,
            comparison=comparison,
            historical_completeness_note="Completion events from Stage 2E onward reflect full activity history. Pre-Stage 2E records reflect task.completed_at where available.",
        )

    # ---------------------------------------------------------
    # 3. Consistency Analytics & Heatmap
    # ---------------------------------------------------------
    def get_consistency(
        self,
        user_id: uuid.UUID,
        tz_name: Optional[str] = "UTC",
    ) -> ConsistencyAnalyticsResponse:
        """
        Calculates current streak, longest streak, weekday productivity distribution,
        and 365-day calendar heatmap.
        """
        tz = self._validate_timezone(tz_name)
        now_local = datetime.now(tz)
        today_local = now_local.date()

        # Query past 365 days of completion episodes
        # Window: [today_local - 364 days, today_local]
        start_365 = today_local - timedelta(days=364)
        dt_start_utc = datetime(start_365.year, start_365.month, start_365.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
        dt_end_utc = datetime(today_local.year, today_local.month, today_local.day, 23, 59, 59, 999999, tzinfo=tz).astimezone(timezone.utc)

        # Also query earlier episodes to calculate all-time longest streak
        # (Fetch all completions for user)
        all_time_start_utc = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        all_episodes = self.repo.get_raw_completion_episodes(user_id, all_time_start_utc, dt_end_utc)

        # Count gross completion events per local day
        # Reopening events do NOT erase a recorded productive day (qualifying completion was performed)
        all_completed_days = set()
        day_completion_counts = defaultdict(int)
        weekday_counts = {
            "Monday": 0, "Tuesday": 0, "Wednesday": 0,
            "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0
        }
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for dt_utc, _, action in all_episodes:
            if action == "COMPLETED":
                d_local = dt_utc.astimezone(tz).date()
                all_completed_days.add(d_local)
                day_completion_counts[d_local] += 1
                w_name = weekday_names[d_local.weekday()]
                weekday_counts[w_name] += 1

        # Calculate Current Streak
        # A streak is active if today is productive, OR if yesterday was productive (when today has no completions yet)
        current_streak = 0
        test_day = today_local
        if test_day not in all_completed_days:
            test_day = today_local - timedelta(days=1)

        while test_day in all_completed_days:
            current_streak += 1
            test_day -= timedelta(days=1)

        # Calculate Longest Streak (across all recorded history)
        longest_streak = 0
        if all_completed_days:
            sorted_days = sorted(list(all_completed_days))
            temp_streak = 1
            longest_streak = 1
            for i in range(1, len(sorted_days)):
                if sorted_days[i] == sorted_days[i - 1] + timedelta(days=1):
                    temp_streak += 1
                else:
                    temp_streak = 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak

        # Most Productive Weekday
        most_productive_weekday = None
        max_wd_completions = -1
        for wd_name in weekday_names:
            if weekday_counts[wd_name] > max_wd_completions and weekday_counts[wd_name] > 0:
                max_wd_completions = weekday_counts[wd_name]
                most_productive_weekday = wd_name

        # Build 365-day Heatmap
        heatmap: List[HeatmapCell] = []
        curr_d = start_365
        while curr_d <= today_local:
            cnt = day_completion_counts.get(curr_d, 0)
            # Level: 0 = 0, 1 = 1-2, 2 = 3-4, 3 = 5-7, 4 = 8+
            if cnt == 0:
                lvl = 0
            elif cnt <= 2:
                lvl = 1
            elif cnt <= 4:
                lvl = 2
            elif cnt <= 7:
                lvl = 3
            else:
                lvl = 4

            heatmap.append(
                HeatmapCell(
                    date=curr_d.isoformat(),
                    count=cnt,
                    level=lvl,
                )
            )
            curr_d += timedelta(days=1)

        return ConsistencyAnalyticsResponse(
            current_streak_days=current_streak,
            longest_streak_days=longest_streak,
            most_productive_weekday=most_productive_weekday,
            weekday_completion_distribution=weekday_counts,
            timezone=tz_name or "UTC",
            total_productive_days=len(all_completed_days),
            heatmap_365_days=heatmap,
        )

    # ---------------------------------------------------------
    # 4. Project Analytics
    # ---------------------------------------------------------
    def get_projects(self, user_id: uuid.UUID) -> ProjectAnalyticsResponse:
        """Returns project-level task counts and progress."""
        now_utc = datetime.now(timezone.utc)
        items = self.repo.get_projects_analytics(user_id, now_utc)
        parsed = [ProjectAnalyticsItem(**item) for item in items]
        return ProjectAnalyticsResponse(projects=parsed, total_projects=len(parsed))

    # ---------------------------------------------------------
    # 5. Category Analytics
    # ---------------------------------------------------------
    def get_categories(self, user_id: uuid.UUID) -> CategoryAnalyticsResponse:
        """Returns category-level task distribution and completion rates."""
        items = self.repo.get_categories_analytics(user_id)
        parsed = [CategoryAnalyticsItem(**item) for item in items]
        return CategoryAnalyticsResponse(categories=parsed, total_categories=len(parsed))

    # ---------------------------------------------------------
    # 6. Workload Analytics
    # ---------------------------------------------------------
    def get_workload(
        self,
        user_id: uuid.UUID,
        tz_name: Optional[str] = "UTC",
    ) -> WorkloadAnalyticsResponse:
        """
        Calculates priority breakdown and non-overlapping due-date horizon distributions
        in user local timezone.
        """
        tz = self._validate_timezone(tz_name)
        now_local = datetime.now(tz)
        today_local = now_local.date()
        tomorrow_local = today_local + timedelta(days=1)
        next_7_end_local = today_local + timedelta(days=7)

        tasks = self.repo.get_pending_tasks_for_workload(user_id)

        priority_dist = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        horizons = {
            "overdue": 0,
            "due_today": 0,
            "due_tomorrow": 0,
            "due_next_7_days": 0,
            "due_later": 0,
            "no_due_date": 0,
        }

        for pri, due_dt in tasks:
            # Priority
            p_val = pri.value.lower() if hasattr(pri, "value") else str(pri).lower()
            if p_val in priority_dist:
                priority_dist[p_val] += 1

            # Horizons (mutually exclusive)
            if due_dt is None:
                horizons["no_due_date"] += 1
            else:
                due_dt_aware = due_dt if due_dt.tzinfo else due_dt.replace(tzinfo=timezone.utc)
                due_d = due_dt_aware.astimezone(tz).date()
                if due_d < today_local:
                    horizons["overdue"] += 1
                elif due_d == today_local:
                    horizons["due_today"] += 1
                elif due_d == tomorrow_local:
                    horizons["due_tomorrow"] += 1
                elif today_local < due_d <= next_7_end_local:
                    horizons["due_next_7_days"] += 1
                else:
                    horizons["due_later"] += 1

        return WorkloadAnalyticsResponse(
            total_pending_tasks=len(tasks),
            priority_distribution=PriorityDistribution(**priority_dist),
            horizons=WorkloadHorizonBreakdown(**horizons),
            timezone=tz_name or "UTC",
        )

    # ---------------------------------------------------------
    # 7. Recurring Task Analytics
    # ---------------------------------------------------------
    def get_recurring(
        self,
        user_id: uuid.UUID,
        tz_name: Optional[str] = "UTC",
    ) -> RecurringAnalyticsResponse:
        """
        Computes recurring task adherence using accurate eligible-occurrence denominator:
        eligible_due = completed_occurrences + pending_due_occurrences + skipped_due_occurrences.
        """
        tz = self._validate_timezone(tz_name)
        today_local = datetime.now(tz).date()

        data = self.repo.get_recurring_analytics_data(user_id, today_local)
        freq_bd = RecurringFrequencyBreakdown(**data["frequency_breakdown"])

        return RecurringAnalyticsResponse(
            total_series=data["total_series"],
            active_series=data["active_series"],
            paused_or_stopped_series=data["paused_or_stopped_series"],
            total_generated_occurrences=data["total_generated_occurrences"],
            completed_occurrences=data["completed_occurrences"],
            pending_due_occurrences=data["pending_due_occurrences"],
            future_occurrences=data["future_occurrences"],
            skipped_occurrences=data["skipped_occurrences"],
            eligible_due_occurrences=data["eligible_due_occurrences"],
            adherence_rate=data["adherence_rate"],
            frequency_breakdown=freq_bd,
            schema_limitations_note="Eligible denominator includes completed occurrences, pending occurrences due on or before today, and explicit skips up to today. Future ungenerated dates are excluded.",
        )
