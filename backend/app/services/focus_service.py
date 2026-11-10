import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.focus import FocusSession, FocusPreference
from app.models.project import Project
from app.models.reminder import Notification
from app.models.task import Task
from app.repositories.focus_repository import FocusRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.focus import (
    FocusAnalyticsOverview,
    FocusDailySummary,
    FocusPreferenceResponse,
    FocusPreferenceUpdate,
    FocusProjectBreakdownItem,
    FocusSessionResponse,
    FocusSessionStart,
    FocusTaskBreakdownItem,
    FocusTrendDay,
    FocusWeeklyTrends,
)


class FocusService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FocusRepository(db)
        self.notif_repo = NotificationRepository(db)

    def _validate_task_and_project(
        self, user_id: uuid.UUID, task_id: Optional[uuid.UUID], project_id: Optional[uuid.UUID]
    ) -> None:
        if task_id:
            task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated task not found or does not belong to you",
                )
            if not project_id and task.project_id:
                project_id = task.project_id

        if project_id:
            project = self.db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated project not found or does not belong to you",
                )

    def _calculate_timing(self, session: FocusSession, current_time: Optional[datetime] = None) -> tuple[int, int, bool]:
        """Calculates (actual_duration_seconds, remaining_seconds, is_expired) strictly from persisted timestamps."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        if session.status == "COMPLETED":
            return session.actual_duration_seconds, 0, True
        elif session.status == "ABANDONED":
            return session.actual_duration_seconds, 0, False

        # Session is ACTIVE or PAUSED
        accumulated_pause = session.accumulated_pause_seconds
        if session.status == "PAUSED" and session.paused_at:
            paused_at = session.paused_at
            if paused_at.tzinfo is None:
                paused_at = paused_at.replace(tzinfo=timezone.utc)
            current_pause = int((current_time - paused_at).total_seconds())
            accumulated_pause += max(0, current_pause)
            effective_elapsed = int((paused_at - started_at).total_seconds()) - session.accumulated_pause_seconds
        else:
            effective_elapsed = int((current_time - started_at).total_seconds()) - accumulated_pause

        effective_elapsed = max(0, effective_elapsed)
        remaining = max(0, session.planned_duration_seconds - effective_elapsed)
        is_expired = remaining == 0
        actual_duration = min(effective_elapsed, session.planned_duration_seconds)

        return actual_duration, remaining, is_expired

    def _serialize_session(self, session: FocusSession, current_time: Optional[datetime] = None) -> FocusSessionResponse:
        actual_dur, remaining, is_expired = self._calculate_timing(session, current_time)
        return FocusSessionResponse(
            id=session.id,
            user_id=session.user_id,
            task_id=session.task_id,
            project_id=session.project_id,
            session_type=session.session_type,
            status=session.status,
            planned_duration_seconds=session.planned_duration_seconds,
            actual_duration_seconds=actual_dur if session.status in ["ACTIVE", "PAUSED"] else session.actual_duration_seconds,
            accumulated_pause_seconds=session.accumulated_pause_seconds,
            started_at=session.started_at,
            paused_at=session.paused_at,
            completed_at=session.completed_at,
            notes=session.notes,
            created_at=session.created_at,
            updated_at=session.updated_at,
            remaining_seconds=remaining,
            is_expired=is_expired,
            task_title=session.task.title if session.task else None,
            project_name=session.project.name if session.project else None,
        )

    def get_or_create_preferences(self, user_id: uuid.UUID) -> FocusPreference:
        pref = self.repo.get_preference(user_id)
        if not pref:
            pref = FocusPreference(
                user_id=user_id,
                focus_duration_minutes=25,
                short_break_duration_minutes=5,
                long_break_duration_minutes=15,
                long_break_interval=4,
                auto_start_breaks=False,
                auto_start_focus=False,
                sound_enabled=True,
                browser_notifications_enabled=True,
                daily_goal_minutes=120,
            )
            try:
                pref = self.repo.create_preference(pref)
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                pref = self.repo.get_preference(user_id)
        return pref

    def update_preferences(self, user_id: uuid.UUID, data: FocusPreferenceUpdate) -> FocusPreference:
        pref = self.get_or_create_preferences(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pref, key, value)
        updated = self.repo.update_preference(pref)
        self.db.commit()
        return updated

    def get_active_session(self, user_id: uuid.UUID) -> Optional[FocusSessionResponse]:
        session = self.repo.get_active_session(user_id)
        if not session:
            return None

        # Check if expired while user was away
        actual_dur, remaining, is_expired = self._calculate_timing(session)
        if is_expired and session.status == "ACTIVE":
            # Auto-complete expired session cleanly
            return self.complete_session(user_id, session.id)

        return self._serialize_session(session)

    def start_session(self, user_id: uuid.UUID, data: FocusSessionStart) -> FocusSessionResponse:
        self._validate_task_and_project(user_id, data.task_id, data.project_id)
        pref = self.get_or_create_preferences(user_id)

        # 1. Atomic concurrency check: Lock user's active session query
        existing = self.repo.get_active_session(user_id, lock=True)
        if existing:
            # If expired, auto-complete it
            _, remaining, is_expired = self._calculate_timing(existing)
            if is_expired:
                self.complete_session(user_id, existing.id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active or paused focus session is already running. Complete or abandon it first.",
                )

        # 2. Determine planned duration
        now = datetime.now(timezone.utc)
        if data.custom_duration_minutes:
            duration_minutes = data.custom_duration_minutes
        elif data.session_type == "SHORT_BREAK":
            duration_minutes = pref.short_break_duration_minutes
        elif data.session_type == "LONG_BREAK":
            duration_minutes = pref.long_break_duration_minutes
        else:
            duration_minutes = pref.focus_duration_minutes

        planned_seconds = duration_minutes * 60

        new_session = FocusSession(
            user_id=user_id,
            task_id=data.task_id,
            project_id=data.project_id,
            session_type=data.session_type,
            status="ACTIVE",
            planned_duration_seconds=planned_seconds,
            actual_duration_seconds=0,
            accumulated_pause_seconds=0,
            started_at=now,
            notes=data.notes,
        )
        try:
            created = self.repo.create(new_session)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active or paused focus session is already running. Complete or abandon it first.",
            )
        return self._serialize_session(created, now)

    def pause_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status == "PAUSED":
            return self._serialize_session(session)
        if session.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pause session in {session.status} state",
            )

        now = datetime.now(timezone.utc)
        session.status = "PAUSED"
        session.paused_at = now
        updated = self.repo.update(session)
        self.db.commit()
        return self._serialize_session(updated, now)

    def resume_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status == "ACTIVE":
            return self._serialize_session(session)
        if session.status != "PAUSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume session in {session.status} state",
            )

        now = datetime.now(timezone.utc)
        if session.paused_at:
            paused_at = session.paused_at
            if paused_at.tzinfo is None:
                paused_at = paused_at.replace(tzinfo=timezone.utc)
            pause_delta = int((now - paused_at).total_seconds())
            session.accumulated_pause_seconds += max(0, pause_delta)

        session.status = "ACTIVE"
        session.paused_at = None
        updated = self.repo.update(session)
        self.db.commit()
        return self._serialize_session(updated, now)

    def complete_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status == "COMPLETED":
            return self._serialize_session(session)
        if session.status not in ["ACTIVE", "PAUSED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete session in {session.status} state",
            )

        now = datetime.now(timezone.utc)
        actual_dur, _, _ = self._calculate_timing(session, now)

        session.status = "COMPLETED"
        session.completed_at = now
        session.actual_duration_seconds = actual_dur
        session.paused_at = None

        updated = self.repo.update(session)

        # Trigger in-app notification if session completed successfully
        try:
            notif_title = f"{session.session_type.replace('_', ' ').title()} Session Completed!"
            dur_mins = round(actual_dur / 60)
            task_info = f" on task '{session.task.title}'" if session.task else ""
            notif_msg = f"Great work! You completed {dur_mins} minute(s) of focus{task_info}."
            notif = Notification(
                user_id=user_id,
                task_id=session.task_id,
                title=notif_title,
                message=notif_msg,
                type="SYSTEM",
            )
            self.notif_repo.create(notif)
        except Exception:
            # Failure in notification creation should not block session completion
            pass

        self.db.commit()
        return self._serialize_session(updated, now)

    def abandon_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status == "ABANDONED":
            return self._serialize_session(session)
        if session.status not in ["ACTIVE", "PAUSED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot abandon session in {session.status} state",
            )

        now = datetime.now(timezone.utc)
        actual_dur, _, _ = self._calculate_timing(session, now)

        session.status = "ABANDONED"
        session.completed_at = now
        session.actual_duration_seconds = actual_dur
        session.paused_at = None

        updated = self.repo.update(session)
        self.db.commit()
        return self._serialize_session(updated, now)

    def get_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self._serialize_session(session)

    def skip_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSessionResponse:
        """Skip current session and transition safely to next configured session.

        If a session is active or paused, it is abandoned or completed with zero recorded duration,
        and the next session type in the Pomodoro cycle is started automatically.
        """
        session = self.repo.get_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status not in ["ACTIVE", "PAUSED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot skip session in {session.status} state",
            )

        now = datetime.now(timezone.utc)
        # Mark current session as abandoned/skipped
        session.status = "ABANDONED"
        session.completed_at = now
        session.actual_duration_seconds = 0
        session.paused_at = None
        self.repo.update(session)
        self.db.commit()

        # Determine next session type in Pomodoro cycle
        pref = self.get_or_create_preferences(user_id)
        if session.session_type == "FOCUS":
            # Check completed count today to see if next is long break
            history = self.repo.list_sessions(user_id=user_id, status="COMPLETED", session_type="FOCUS", limit=pref.long_break_interval)
            completed_focus_count = len(history)
            next_type = "LONG_BREAK" if (completed_focus_count % pref.long_break_interval == 0 and completed_focus_count > 0) else "SHORT_BREAK"
        else:
            next_type = "FOCUS"

        # Start next session
        next_start_data = FocusSessionStart(
            session_type=next_type,
            task_id=session.task_id if next_type == "FOCUS" else None,
            project_id=session.project_id if next_type == "FOCUS" else None,
            notes=f"Auto-transitioned after skipping previous session",
        )
        return self.start_session(user_id, next_start_data)
    def list_history(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[str] = None,
        session_type: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[FocusSessionResponse]:
        sessions = self.repo.list_sessions(
            user_id=user_id,
            status=status_filter,
            session_type=session_type,
            task_id=task_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
        return [self._serialize_session(s) for s in sessions]

    def get_analytics_overview(
        self, user_id: uuid.UUID, timezone_str: str = "UTC"
    ) -> FocusAnalyticsOverview:
        try:
            tz = ZoneInfo(timezone_str)
        except Exception:
            tz = timezone.utc

        now_utc = datetime.now(timezone.utc)
        local_now = now_utc.astimezone(tz)
        pref = self.get_or_create_preferences(user_id)

        # 1. Daily Summary (today in user timezone)
        start_of_today_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_today_utc = start_of_today_local.astimezone(timezone.utc)
        end_of_today_local = start_of_today_local + timedelta(days=1) - timedelta(microseconds=1)
        end_of_today_utc = end_of_today_local.astimezone(timezone.utc)

        today_sessions = self.repo.get_completed_focus_sessions_in_range(
            user_id, start_of_today_utc, end_of_today_utc
        )
        today_focus_seconds = sum(s.actual_duration_seconds for s in today_sessions)
        today_completed_count = len(today_sessions)
        goal_minutes = pref.daily_goal_minutes
        goal_pct = min(100.0, round((today_focus_seconds / 60) / goal_minutes * 100, 1)) if goal_minutes > 0 else 0.0

        daily_summary = FocusDailySummary(
            today_focus_seconds=today_focus_seconds,
            today_completed_sessions=today_completed_count,
            daily_goal_minutes=goal_minutes,
            goal_completion_percentage=goal_pct,
            streak_days=1 if today_completed_count > 0 else 0,
        )

        # 2. Weekly Trends (last 7 days)
        start_of_week_local = start_of_today_local - timedelta(days=6)
        start_of_week_utc = start_of_week_local.astimezone(timezone.utc)

        week_sessions = self.repo.get_completed_focus_sessions_in_range(
            user_id, start_of_week_utc, end_of_today_utc
        )

        trend_days: List[FocusTrendDay] = []
        for i in range(7):
            d_local = start_of_week_local + timedelta(days=i)
            d_str = d_local.strftime("%Y-%m-%d")
            d_start_utc = d_local.astimezone(timezone.utc)
            d_end_utc = (d_local + timedelta(days=1) - timedelta(microseconds=1)).astimezone(timezone.utc)
            d_sess = [s for s in week_sessions if d_start_utc <= (s.completed_at if s.completed_at.tzinfo else s.completed_at.replace(tzinfo=timezone.utc)) <= d_end_utc]
            trend_days.append(
                FocusTrendDay(
                    date=d_str,
                    focus_minutes=round(sum(s.actual_duration_seconds for s in d_sess) / 60),
                    completed_sessions=len(d_sess),
                )
            )

        total_week_seconds = sum(s.actual_duration_seconds for s in week_sessions)
        total_week_mins = round(total_week_seconds / 60)
        total_week_count = len(week_sessions)
        avg_session_mins = round(total_week_mins / total_week_count, 1) if total_week_count > 0 else 0.0

        weekly_trends = FocusWeeklyTrends(
            total_focus_minutes=total_week_mins,
            total_completed_sessions=total_week_count,
            average_session_minutes=avg_session_mins,
            days=trend_days,
        )

        # 3. Task Breakdown
        task_map: dict[Optional[uuid.UUID], dict] = {}
        for s in week_sessions:
            t_id = s.task_id
            if t_id not in task_map:
                task_title = s.task.title if s.task else "Unassigned / General Focus"
                task_map[t_id] = {"title": task_title, "seconds": 0, "count": 0}
            task_map[t_id]["seconds"] += s.actual_duration_seconds
            task_map[t_id]["count"] += 1

        task_breakdown = [
            FocusTaskBreakdownItem(
                task_id=tid,
                task_title=info["title"],
                total_focus_minutes=round(info["seconds"] / 60),
                completed_sessions=info["count"],
            )
            for tid, info in task_map.items()
        ]

        # 4. Project Breakdown
        project_map: dict[Optional[uuid.UUID], dict] = {}
        for s in week_sessions:
            p_id = s.project_id
            if p_id not in project_map:
                project_name = s.project.name if s.project else "No Project"
                project_map[p_id] = {"name": project_name, "seconds": 0, "count": 0}
            project_map[p_id]["seconds"] += s.actual_duration_seconds
            project_map[p_id]["count"] += 1

        project_breakdown = [
            FocusProjectBreakdownItem(
                project_id=pid,
                project_name=info["name"],
                total_focus_minutes=round(info["seconds"] / 60),
                completed_sessions=info["count"],
            )
            for pid, info in project_map.items()
        ]

        return FocusAnalyticsOverview(
            daily=daily_summary,
            weekly=weekly_trends,
            task_breakdown=task_breakdown,
            project_breakdown=project_breakdown,
        )
