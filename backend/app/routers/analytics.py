"""
DayFlow backend – analytics router (Stage 4).

Endpoints
---------
GET /analytics
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=schemas.AnalyticsResponse, summary="Get productivity analytics")
def get_analytics(
    days: int = Query(default=84, ge=7, le=365, description="Number of days for heatmap history"),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated productivity analytics including:
    - Overall summary counts (completed, pending, overdue) & completion %
    - Daily metrics for today
    - 7-day completion trend
    - Productivity heatmap based on actual history (Asia/Kolkata timezone)
    - Category & priority breakdowns
    """
    return crud.get_analytics(db=db, days=days)
