import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog


class ActivityLogRepository:
    """Repository handling database operations for activity log audit records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, log: ActivityLog, commit: bool = False) -> ActivityLog:
        """
        Add an activity record to the session.
        By default flush without committing to participate in caller transaction boundaries.
        """
        self.db.add(log)
        if commit:
            self.db.commit()
            self.db.refresh(log)
        else:
            self.db.flush()
        return log

    def list_user_activities(
        self,
        user_id: uuid.UUID,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        recurring_task_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ActivityLog], int]:
        """
        Retrieve paginated activity logs strictly scoped to user_id.
        Sorted deterministically: newest first (created_at DESC, id DESC).
        """
        stmt = select(ActivityLog).where(ActivityLog.user_id == user_id)

        if action:
            stmt = stmt.where(ActivityLog.action == action)
        if entity_type:
            stmt = stmt.where(ActivityLog.entity_type == entity_type)
        if task_id:
            stmt = stmt.where(ActivityLog.task_id == task_id)
        if recurring_task_id:
            stmt = stmt.where(ActivityLog.recurring_task_id == recurring_task_id)
        if start_date:
            stmt = stmt.where(ActivityLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(ActivityLog.created_at <= end_date)

        # Count total
        count_stmt = select(func.count(ActivityLog.id)).where(ActivityLog.user_id == user_id)
        if action:
            count_stmt = count_stmt.where(ActivityLog.action == action)
        if entity_type:
            count_stmt = count_stmt.where(ActivityLog.entity_type == entity_type)
        if task_id:
            count_stmt = count_stmt.where(ActivityLog.task_id == task_id)
        if recurring_task_id:
            count_stmt = count_stmt.where(ActivityLog.recurring_task_id == recurring_task_id)
        if start_date:
            count_stmt = count_stmt.where(ActivityLog.created_at >= start_date)
        if end_date:
            count_stmt = count_stmt.where(ActivityLog.created_at <= end_date)

        total = self.db.execute(count_stmt).scalar() or 0

        # Deterministic ordering
        stmt = stmt.order_by(desc(ActivityLog.created_at), desc(ActivityLog.id)).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())

        return items, total

    def list_task_activities(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ActivityLog], int]:
        """
        Retrieve paginated chronological activity timeline for a task strictly owned by user_id.
        """
        stmt = select(ActivityLog).where(
            ActivityLog.task_id == task_id,
            ActivityLog.user_id == user_id,
        )

        count_stmt = select(func.count(ActivityLog.id)).where(
            ActivityLog.task_id == task_id,
            ActivityLog.user_id == user_id,
        )
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(desc(ActivityLog.created_at), desc(ActivityLog.id)).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())

        return items, total

