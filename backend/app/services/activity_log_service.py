import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.activity_log import ActivityLogListResponse, ActivityLogResponse


class ActivityLogService:
    """
    Centralized activity logging service for recording and querying audit trail events.
    All record creation flushes inside the existing SQLAlchemy transaction.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = ActivityLogRepository(db)
        self.task_repo = TaskRepository(db)

    def log_event(
        self,
        user_id: uuid.UUID,
        entity_type: ActivityEntityType,
        entity_id: uuid.UUID,
        action: ActivityAction,
        actor_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        recurring_task_id: Optional[uuid.UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        commit: bool = False,
    ) -> ActivityLog:
        """
        Record a structured activity log entry.
        Never commits by default so caller transaction owns the boundary.
        """
        log = ActivityLog(
            user_id=user_id,
            actor_id=actor_id or user_id,
            task_id=task_id,
            recurring_task_id=recurring_task_id,
            entity_type=entity_type.value if hasattr(entity_type, "value") else str(entity_type),
            entity_id=entity_id,
            action=action.value if hasattr(action, "value") else str(action),
            changes=changes,
            extra_metadata=metadata,
        )
        return self.repo.create(log, commit=commit)

    def list_global_activities(
        self,
        user_id: uuid.UUID,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        recurring_task_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ActivityLogListResponse:
        """
        Query chronological global activity feed strictly owned by the authenticated user.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        items, total = self.repo.list_user_activities(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            task_id=task_id,
            recurring_task_id=recurring_task_id,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            limit=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return ActivityLogListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def list_task_timeline(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ActivityLogListResponse:
        """
        Query activity timeline for a single task.
        Verifies task ownership first; returns 404 if not found or belongs to another user.
        """
        task = self.task_repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        items, total = self.repo.list_task_activities(
            task_id=task_id,
            user_id=user_id,
            offset=offset,
            limit=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return ActivityLogListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def _to_response(log: ActivityLog) -> ActivityLogResponse:
        return ActivityLogResponse(
            id=log.id,
            user_id=log.user_id,
            actor_id=log.actor_id,
            task_id=log.task_id,
            recurring_task_id=log.recurring_task_id,
            entity_type=ActivityEntityType(log.entity_type),
            entity_id=log.entity_id,
            action=ActivityAction(log.action),
            changes=log.changes,
            metadata=log.extra_metadata,
            created_at=log.created_at,
        )

