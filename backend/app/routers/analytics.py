"""
DayFlow backend – analytics router (Stage 4 & 5).

Endpoints
---------
GET /analytics
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=schemas.AnalyticsResponse, summary="Get productivity analytics")
def get_analytics(
    days: int = Query(default=84, ge=7, le=365, description="Number of days for heatmap history"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated productivity analytics for the authenticated user including:
    - Overall summary counts (completed, pending, overdue) & completion %
    - Daily metrics for today
    - 7-day completion trend
    - Productivity heatmap based on actual history (Asia/Kolkata timezone)
    - Category & priority breakdowns
    """
    return crud.get_analytics(db=db, user_id=current_user.id, days=days)
