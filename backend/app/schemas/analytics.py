import uuid
from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductivityOverviewResponse(BaseModel):
    """Productivity Overview KPIs for the user."""
    total_tasks: int = Field(..., description="Total non-archived root tasks")
    completed_tasks: int = Field(..., description="Currently completed non-archived root tasks")
    pending_tasks: int = Field(..., description="Active pending tasks (TODO + IN_PROGRESS)")
    overdue_tasks: int = Field(..., description="Pending tasks past due_date")
    cancelled_tasks: int = Field(..., description="Currently cancelled tasks")
    completion_rate: float = Field(..., description="Percentage: completed / (completed + pending)")
    
    # Range specific
    period_start: datetime = Field(..., description="Start of selected analysis period (UTC)")
    period_end: datetime = Field(..., description="End of selected analysis period (UTC)")
    tasks_created_in_period: int = Field(..., description="Tasks created during selected period")
    tasks_completed_in_period: int = Field(..., description="Gross task completion episodes during selected period")
    tasks_reopened_in_period: int = Field(..., description="Task reopening events during selected period")
    net_completions_in_period: int = Field(..., description="Net completed tasks in selected period (gross completions - reopening events; can be negative)")

    model_config = ConfigDict(from_attributes=True)


class TrendBucket(BaseModel):
    """Time-series bucket for daily/weekly/monthly completion trends."""
    bucket_label: str = Field(..., description="Date or bucket label (YYYY-MM-DD or YYYY-WW or YYYY-MM)")
    start_date: str = Field(..., description="Bucket start date")
    end_date: str = Field(..., description="Bucket end date")
    created_count: int = Field(0, description="Tasks created in bucket")
    gross_completions: int = Field(0, description="Gross completion events/episodes in bucket")
    reopened_count: int = Field(0, description="Reopened events in bucket")
    net_completions: int = Field(0, description="Net completions (gross_completions - reopened_count; can be negative)")
    unique_tasks_completed: int = Field(0, description="Unique distinct tasks completed in bucket")


class PeriodComparison(BaseModel):
    """Comparison between current period and prior equal-length period."""
    current_period_completions: int
    prior_period_completions: int
    completion_change_percentage: Optional[float] = None
    current_period_created: int
    prior_period_created: int
    created_change_percentage: Optional[float] = None


class ProductivityTrendsResponse(BaseModel):
    """Aggregated productivity trend series."""
    interval: str = Field(..., description="Aggregation interval: daily, weekly, or monthly")
    timezone: str = Field(..., description="IANA Timezone used for date boundaries")
    period_start: str = Field(..., description="Analysis window start date")
    period_end: str = Field(..., description="Analysis window end date")
    buckets: List[TrendBucket] = Field(default_factory=list)
    comparison: PeriodComparison
    historical_completeness_note: str = Field(
        ...,
        description="Documentation explaining data sources (Stage 2E activity events vs pre-Stage 2E completed_at)",
    )

    model_config = ConfigDict(from_attributes=True)


class HeatmapCell(BaseModel):
    """Single calendar day entry for 365-day productivity heatmap."""
    date: str = Field(..., description="Calendar date YYYY-MM-DD in user timezone")
    count: int = Field(0, description="Number of qualifying completion episodes on this day")
    level: int = Field(0, description="Intensity level from 0 (none) to 4 (high)")


class ConsistencyAnalyticsResponse(BaseModel):
    """Habit, streak and calendar consistency analytics."""
    current_streak_days: int = Field(..., description="Consecutive productive days ending today or yesterday")
    longest_streak_days: int = Field(..., description="Longest consecutive productive days recorded")
    most_productive_weekday: Optional[str] = Field(None, description="Weekday with highest completion count (e.g. Monday)")
    weekday_completion_distribution: Dict[str, int] = Field(default_factory=dict, description="Completions by weekday name")
    timezone: str = Field(..., description="IANA timezone evaluated")
    total_productive_days: int = Field(..., description="Total unique calendar days with >= 1 completion")
    heatmap_365_days: List[HeatmapCell] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProjectAnalyticsItem(BaseModel):
    """Project-level task distribution and progress metrics."""
    project_id: uuid.UUID
    project_name: str
    project_color: Optional[str] = None
    project_status: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_percentage: float

    model_config = ConfigDict(from_attributes=True)


class ProjectAnalyticsResponse(BaseModel):
    """Project analytics list response."""
    projects: List[ProjectAnalyticsItem]
    total_projects: int


class CategoryAnalyticsItem(BaseModel):
    """Category-level task distribution and progress metrics."""
    category_id: Optional[uuid.UUID] = None
    category_name: str
    category_color: Optional[str] = None
    category_icon: Optional[str] = None
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completion_rate: float

    model_config = ConfigDict(from_attributes=True)


class CategoryAnalyticsResponse(BaseModel):
    """Category analytics response including uncategorized bucket."""
    categories: List[CategoryAnalyticsItem]
    total_categories: int


class WorkloadHorizonBreakdown(BaseModel):
    """Distribution of pending tasks across mutually exclusive due-date horizons."""
    overdue: int = Field(..., description="Due date is past (prior to today in user timezone)")
    due_today: int = Field(..., description="Due date falls within today in user timezone")
    due_tomorrow: int = Field(..., description="Due date falls on tomorrow in user timezone")
    due_next_7_days: int = Field(..., description="Due date falls between day 2 and day 7 in user timezone")
    due_later: int = Field(..., description="Due date is beyond 7 days")
    no_due_date: int = Field(..., description="Pending tasks without a due date")


class PriorityDistribution(BaseModel):
    """Pending tasks count grouped by priority."""
    urgent: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class WorkloadAnalyticsResponse(BaseModel):
    """Workload and upcoming deadline distribution for pending tasks."""
    total_pending_tasks: int
    priority_distribution: PriorityDistribution
    horizons: WorkloadHorizonBreakdown
    timezone: str

    model_config = ConfigDict(from_attributes=True)


class RecurringFrequencyBreakdown(BaseModel):
    """Recurring series count grouped by frequency."""
    daily: int = 0
    weekly: int = 0
    monthly: int = 0
    yearly: int = 0
    custom: int = 0


class RecurringAnalyticsResponse(BaseModel):
    """Recurring tasks adherence and execution analytics."""
    total_series: int = Field(..., description="Total recurring task series created by user")
    active_series: int = Field(..., description="Currently active recurring series")
    paused_or_stopped_series: int = Field(..., description="Currently paused or stopped series")
    total_generated_occurrences: int = Field(..., description="Total task occurrence instances materialized")
    completed_occurrences: int = Field(..., description="Generated occurrences marked COMPLETED")
    pending_due_occurrences: int = Field(..., description="Generated occurrences past due or due today that remain pending")
    future_occurrences: int = Field(..., description="Generated occurrences scheduled strictly in the future")
    skipped_occurrences: int = Field(..., description="Dates deliberately skipped via recurring skips")
    eligible_due_occurrences: int = Field(..., description="Eligible denominator: completed + pending_due + skipped")
    adherence_rate: float = Field(
        ...,
        description="Percentage of completed occurrences relative to eligible due occurrences: completed / eligible_due * 100",
    )
    frequency_breakdown: RecurringFrequencyBreakdown
    schema_limitations_note: str = Field(
        ...,
        description="Notes on recurring task historical calculation boundaries",
    )

    model_config = ConfigDict(from_attributes=True)

