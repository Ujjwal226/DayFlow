import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session

from app.models.focus import FocusSession, FocusPreference


class FocusRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FocusSession]:
        query = select(FocusSession).where(
            and_(FocusSession.id == session_id, FocusSession.user_id == user_id)
        )
        return self.db.scalars(query).first()

    def get_active_session(self, user_id: uuid.UUID, lock: bool = False) -> Optional[FocusSession]:
        """Finds any session that is currently ACTIVE or PAUSED for the user."""
        query = select(FocusSession).where(
            and_(
                FocusSession.user_id == user_id,
                FocusSession.status.in_(["ACTIVE", "PAUSED"]),
            )
        ).order_by(FocusSession.started_at.desc())

        if lock:
            bind = self.db.get_bind()
            if bind and bind.dialect.name == "postgresql":
                query = query.with_for_update()
            elif bind and bind.dialect.name != "sqlite":
                query = query.with_for_update()

        return self.db.scalars(query).first()

    def list_sessions(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[FocusSession]:
        query = select(FocusSession).where(FocusSession.user_id == user_id)
        if status:
            query = query.where(FocusSession.status == status)
        if session_type:
            query = query.where(FocusSession.session_type == session_type)
        if task_id:
            query = query.where(FocusSession.task_id == task_id)
        if project_id:
            query = query.where(FocusSession.project_id == project_id)

        query = query.order_by(FocusSession.started_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(query).all())

    def create(self, session: FocusSession) -> FocusSession:
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)
        return session

    def update(self, session: FocusSession) -> FocusSession:
        self.db.flush()
        self.db.refresh(session)
        return session

    def get_preference(self, user_id: uuid.UUID) -> Optional[FocusPreference]:
        query = select(FocusPreference).where(FocusPreference.user_id == user_id)
        return self.db.scalars(query).first()

    def create_preference(self, pref: FocusPreference) -> FocusPreference:
        self.db.add(pref)
        self.db.flush()
        self.db.refresh(pref)
        return pref

    def update_preference(self, pref: FocusPreference) -> FocusPreference:
        self.db.flush()
        self.db.refresh(pref)
        return pref

    def get_completed_focus_sessions_in_range(
        self, user_id: uuid.UUID, start_time: datetime, end_time: datetime
    ) -> List[FocusSession]:
        """Returns completed FOCUS sessions between start_time and end_time."""
        query = select(FocusSession).where(
            and_(
                FocusSession.user_id == user_id,
                FocusSession.session_type == "FOCUS",
                FocusSession.status == "COMPLETED",
                FocusSession.completed_at >= start_time,
                FocusSession.completed_at <= end_time,
            )
        ).order_by(FocusSession.completed_at.asc())
        return list(self.db.scalars(query).all())
