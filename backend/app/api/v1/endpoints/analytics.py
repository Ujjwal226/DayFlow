from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    CategoryAnalyticsResponse,
    ConsistencyAnalyticsResponse,
    ProductivityOverviewResponse,
    ProductivityTrendsResponse,
    ProjectAnalyticsResponse,
    RecurringAnalyticsResponse,
    WorkloadAnalyticsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Productivity Analytics"])


@router.get(
    "/overview",
    response_model=ProductivityOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get productivity overview KPIs",
)
def get_productivity_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for created/completed counts in UTC"),
    end_date: Optional[datetime] = Query(None, description="End date for created/completed counts in UTC"),
    days: int = Query(30, ge=1, le=366, description="Default trailing window if dates omitted"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductivityOverviewResponse:
    """Retrieve high-level task metrics and completion performance for authenticated user."""
    service = AnalyticsService(db)
    return service.get_overview(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )


@router.get(
    "/trends",
    response_model=ProductivityTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get time-series productivity trends",
)
def get_productivity_trends(
    interval: str = Query("daily", description="Aggregation interval: daily, weekly, or monthly"),
    days: Optional[int] = Query(30, ge=1, le=366, description="Trailing days count (e.g. 7, 30, 90)"),
    start_date: Optional[date] = Query(None, description="Explicit range start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Explicit range end date (YYYY-MM-DD)"),
    timezone: str = Query("UTC", description="IANA timezone for day boundaries (e.g. America/New_York)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductivityTrendsResponse:
    """Retrieve zero-filled time-series buckets of completed and created tasks with period comparisons."""
    service = AnalyticsService(db)
    return service.get_trends(
        user_id=current_user.id,
        interval=interval,
        days=days,
        start_date=start_date,
        end_date=end_date,
        tz_name=timezone,
    )


@router.get(
    "/consistency",
    response_model=ConsistencyAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get consistency streaks and 365-day calendar heatmap",
)
def get_consistency_analytics(
    timezone: str = Query("UTC", description="IANA timezone for calendar day boundaries"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsistencyAnalyticsResponse:
    """Retrieve current streak, longest streak, most productive weekdays, and 365-day completion intensity heatmap."""
    service = AnalyticsService(db)
    return service.get_consistency(
        user_id=current_user.id,
        tz_name=timezone,
    )


@router.get(
    "/projects",
    response_model=ProjectAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project-wise task distribution and progress",
)
def get_projects_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectAnalyticsResponse:
    """Retrieve project performance breakdown with task counts, completion percentages, and overdues."""
    service = AnalyticsService(db)
    return service.get_projects(user_id=current_user.id)


@router.get(
    "/categories",
    response_model=CategoryAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category-wise task distribution and completion rates",
)
def get_categories_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryAnalyticsResponse:
    """Retrieve category performance breakdown including uncategorized tasks."""
    service = AnalyticsService(db)
    return service.get_categories(user_id=current_user.id)


@router.get(
    "/workload",
    response_model=WorkloadAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workload and upcoming deadline horizons",
)
def get_workload_analytics(
    timezone: str = Query("UTC", description="IANA timezone for due date boundaries"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkloadAnalyticsResponse:
    """Retrieve priority distribution and mutually exclusive deadline horizons for all active pending tasks."""
    service = AnalyticsService(db)
    return service.get_workload(
        user_id=current_user.id,
        tz_name=timezone,
    )


@router.get(
    "/recurring",
    response_model=RecurringAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recurring tasks adherence and execution analytics",
)
def get_recurring_analytics(
    timezone: str = Query("UTC", description="IANA timezone for day comparison"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringAnalyticsResponse:
    """Retrieve recurring task series adherence, skipped occurrences, and frequency breakdowns."""
    service = AnalyticsService(db)
    return service.get_recurring(
        user_id=current_user.id,
        tz_name=timezone,
    )

