import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.activity_log import ActivityAction, ActivityEntityType
from app.models.user import User
from app.schemas.activity_log import ActivityLogListResponse
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=ActivityLogListResponse)
def get_global_activity_feed(
    action: Optional[str] = Query(None, description="Filter by activity action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    task_id: Optional[uuid.UUID] = Query(None, description="Filter by task UUID"),
    recurring_task_id: Optional[uuid.UUID] = Query(None, description="Filter by recurring series UUID"),
    start_date: Optional[datetime] = Query(None, description="Filter from timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter up to timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityLogListResponse:
    """
    Retrieve chronological global activity feed strictly belonging to current authenticated user.
    """
    service = ActivityLogService(db)
    return service.list_global_activities(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        task_id=task_id,
        recurring_task_id=recurring_task_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

