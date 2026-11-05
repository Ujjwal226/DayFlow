import math
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.recurring_task import RecurrenceFrequency, RecurringTask, RecurringTaskSkip
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.activity_log import ActivityAction, ActivityEntityType, ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.recurring_task_repository import RecurringTaskRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.recurring_task import (
    RecurringTaskCreateRequest,
    RecurringTaskListResponse,
    RecurringTaskResponse,
    RecurringTaskSkipRequest,
    RecurringTaskUpdateRequest,
)
from app.schemas.task import TaskListResponse
from app.services.recurrence_calculator import (
    calculate_next_occurrence,
    is_valid_recurrence_date,
)


class RecurringTaskService:
    """Business logic for recurring task templates, lifecycle states, and occurrence generation."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RecurringTaskRepository(db)
        self.task_repo = TaskRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    def _parse_weekdays_from_str(self, weekdays_str: Optional[str]) -> Optional[List[int]]:
        if not weekdays_str:
            return None
        try:
            return [int(x) for x in weekdays_str.split(",") if x.strip()]
        except ValueError:
            return None

    def _format_weekdays_to_str(self, weekdays_list: Optional[List[int]]) -> Optional[str]:
        if not weekdays_list:
            return None
        return ",".join(str(x) for x in sorted(set(weekdays_list)))

    def _to_response(self, series: RecurringTask) -> RecurringTaskResponse:
        data = {
            "id": series.id,
            "user_id": series.user_id,
            "title": series.title,
            "description": series.description,
            "priority": series.priority,
            "category_id": series.category_id,
            "category": series.category,
            "project_id": series.project_id,
            "frequency": series.frequency,
            "interval": series.interval,
            "start_date": series.start_date,
            "end_date": series.end_date,
            "max_occurrences": series.max_occurrences,
            "weekdays": self._parse_weekdays_from_str(series.weekdays),
            "day_of_month": series.day_of_month,
            "month_of_year": series.month_of_year,
            "timezone": series.timezone,
            "next_occurrence_date": series.next_occurrence_date,
            "occurrences_generated": series.occurrences_generated,
            "is_active": series.is_active,
            "is_stopped": series.is_stopped,
            "created_at": series.created_at,
            "updated_at": series.updated_at,
        }
        return RecurringTaskResponse.model_validate(data)

    def create_series(self, user_id: uuid.UUID, payload: RecurringTaskCreateRequest) -> RecurringTaskResponse:
        # Validate category ownership if supplied
        if payload.category_id:
            cat = self.cat_repo.get_by_id(payload.category_id, user_id)
            if not cat:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        # Validate project ownership if supplied
        if payload.project_id:
            proj = self.proj_repo.get_by_id(payload.project_id, user_id)
            if not proj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # Start date is the initial occurrence date
        weekdays_str = self._format_weekdays_to_str(payload.weekdays)

        try:
            series = RecurringTask(
                user_id=user_id,
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                category_id=payload.category_id,
                project_id=payload.project_id,
                frequency=payload.frequency,
                interval=payload.interval,
                start_date=payload.start_date,
                end_date=payload.end_date,
                max_occurrences=payload.max_occurrences,
                weekdays=weekdays_str,
                day_of_month=payload.day_of_month,
                month_of_year=payload.month_of_year,
                timezone=payload.timezone or "UTC",
                next_occurrence_date=payload.start_date,
                occurrences_generated=0,
                is_active=True,
                is_stopped=False,
            )
            created = self.repo.create(series, commit=False)

            # Generate initial occurrence within the same atomic transaction (flush without committing yet)
            self._generate_occurrences_for_series(created, cutoff=payload.start_date)

            # Log RECURRING_SERIES_CREATED within the same atomic transaction
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    recurring_task_id=created.id,
                    entity_type=ActivityEntityType.RECURRING_TASK.value,
                    entity_id=created.id,
                    action=ActivityAction.RECURRING_SERIES_CREATED.value,
                    changes=None,
                    extra_metadata={
                        "title": created.title,
                        "frequency": created.frequency.value if hasattr(created.frequency, "value") else str(created.frequency),
                        "interval": created.interval,
                    },
                ),
                commit=False,
            )

            # Commit the unified transaction (series + initial occurrence + activity log) atomically
            self.db.commit()

            fresh = self.repo.get_by_id(created.id, user_id)
            return self._to_response(fresh or created)
        except Exception:
            self.db.rollback()
            raise

    def get_series(self, series_id: uuid.UUID, user_id: uuid.UUID) -> RecurringTaskResponse:
        series = self.repo.get_by_id(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")
        return self._to_response(series)

    def update_series(
        self,
        series_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: RecurringTaskUpdateRequest,
    ) -> RecurringTaskResponse:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")

        # Track changes for activity log
        changes = {}
        old_title = series.title
        old_desc = series.description
        old_pri = series.priority
        old_freq = series.frequency
        old_interval = series.interval
        old_end = series.end_date
        old_max = series.max_occurrences

        if payload.category_id is not None:
            cat = self.cat_repo.get_by_id(payload.category_id, user_id)
            if not cat:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
            series.category_id = payload.category_id

        if payload.project_id is not None:
            proj = self.proj_repo.get_by_id(payload.project_id, user_id)
            if not proj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
            series.project_id = payload.project_id

        if payload.title is not None and payload.title != old_title:
            changes["title"] = {"old": old_title, "new": payload.title}
            series.title = payload.title
        if payload.description is not None and payload.description != old_desc:
            changes["description"] = {"old": old_desc, "new": payload.description}
            series.description = payload.description
        if payload.priority is not None and payload.priority != old_pri:
            changes["priority"] = {
                "old": old_pri.value if hasattr(old_pri, "value") else str(old_pri),
                "new": payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
            }
            series.priority = payload.priority
        schedule_changed = False
        if payload.frequency is not None and payload.frequency != series.frequency:
            changes["frequency"] = {
                "old": old_freq.value if hasattr(old_freq, "value") else str(old_freq),
                "new": payload.frequency.value if hasattr(payload.frequency, "value") else str(payload.frequency),
            }
            series.frequency = payload.frequency
            schedule_changed = True
        if payload.interval is not None and payload.interval != series.interval:
            changes["interval"] = {"old": old_interval, "new": payload.interval}
            series.interval = payload.interval
            schedule_changed = True
        if payload.end_date is not None:
            if payload.end_date < series.start_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="End date cannot be earlier than start date.",
                )
            if payload.end_date != series.end_date:
                changes["end_date"] = {"old": old_end.isoformat() if old_end else None, "new": payload.end_date.isoformat()}
                series.end_date = payload.end_date
                schedule_changed = True
        if payload.max_occurrences is not None:
            if payload.max_occurrences != series.max_occurrences:
                changes["max_occurrences"] = {"old": old_max, "new": payload.max_occurrences}
                series.max_occurrences = payload.max_occurrences
                schedule_changed = True

        if payload.weekdays is not None:
            formatted_weekdays = self._format_weekdays_to_str(payload.weekdays)
            if formatted_weekdays != series.weekdays:
                series.weekdays = formatted_weekdays
                schedule_changed = True
        if payload.day_of_month is not None and payload.day_of_month != series.day_of_month:
            series.day_of_month = payload.day_of_month
            schedule_changed = True
        if payload.month_of_year is not None and payload.month_of_year != series.month_of_year:
            series.month_of_year = payload.month_of_year
            schedule_changed = True

        if schedule_changed and not series.is_stopped:
            # Reconcile future pending occurrences:
            # Protect completed occurrences and individually modified occurrences (e.g. IN_PROGRESS or custom edits).
            # Delete future system-generated TODO occurrences that no longer match the new recurrence schedule.
            today = datetime.now(timezone.utc).date()
            from sqlalchemy import select, delete
            parsed_weekdays = self._parse_weekdays_from_str(series.weekdays)

            future_todo_tasks = list(
                self.db.execute(
                    select(Task).where(
                        Task.recurring_task_id == series.id,
                        Task.user_id == user_id,
                        Task.occurrence_date > today,
                        Task.status == TaskStatus.TODO,
                    )
                ).scalars().all()
            )

            for task in future_todo_tasks:
                if task.occurrence_date:
                    # Detect if the task was individually modified:
                    # 1. Custom title, description, or priority differing from series template
                    # 2. Reassigned category or project
                    # 3. Custom tags attached
                    # 4. Subtasks added
                    # 5. Due date or start date shifted from standard occurrence midnight UTC
                    expected_dt = datetime.combine(task.occurrence_date, datetime.min.time(), tzinfo=timezone.utc)
                    # Normalize task.due_date tzinfo for reliable comparison
                    task_due_normalized = None
                    if task.due_date is not None:
                        task_due_normalized = task.due_date if task.due_date.tzinfo else task.due_date.replace(tzinfo=timezone.utc)

                    is_modified = (
                        task.title != series.title
                        or (task.description or None) != (series.description or None)
                        or task.priority != series.priority
                        or task.category_id != series.category_id
                        or task.project_id != series.project_id
                        or bool(task.tags)
                        or bool(task.subtasks)
                        or (task_due_normalized is not None and task_due_normalized != expected_dt)
                    )
                    # If the task was modified by the user, preserve it even if off-schedule
                    if is_modified:
                        continue

                    is_valid = is_valid_recurrence_date(
                        candidate_date=task.occurrence_date,
                        start_date=series.start_date,
                        frequency=series.frequency,
                        interval=series.interval,
                        weekdays=parsed_weekdays,
                        day_of_month=series.day_of_month,
                        month_of_year=series.month_of_year,
                        end_date=series.end_date,
                    )
                    if not is_valid:
                        self.db.delete(task)

            # Check if series limits already reached
            if (
                series.max_occurrences is not None
                and series.occurrences_generated >= series.max_occurrences
            ):
                series.next_occurrence_date = None
                series.is_stopped = True
            elif series.end_date and series.end_date <= today:
                series.next_occurrence_date = None
                series.is_stopped = True
            else:
                # Recalculate next_occurrence_date strictly from max(series.start_date, today) forward
                calc_base = max(series.start_date, today)
                # Find next valid occurrence strictly >= calc_base
                candidate = calc_base
                if not is_valid_recurrence_date(
                    candidate_date=candidate,
                    start_date=series.start_date,
                    frequency=series.frequency,
                    interval=series.interval,
                    weekdays=parsed_weekdays,
                    day_of_month=series.day_of_month,
                    month_of_year=series.month_of_year,
                    end_date=series.end_date,
                ):
                    candidate = calculate_next_occurrence(
                        current_date=candidate,
                        frequency=series.frequency,
                        interval=series.interval,
                        weekdays=parsed_weekdays,
                        day_of_month=series.day_of_month,
                        month_of_year=series.month_of_year,
                    )

                # Check if skipped or limits exceeded
                while candidate:
                    if series.end_date and candidate > series.end_date:
                        series.next_occurrence_date = None
                        series.is_stopped = True
                        break
                    if (
                        series.max_occurrences is not None
                        and series.occurrences_generated >= series.max_occurrences
                    ):
                        series.next_occurrence_date = None
                        series.is_stopped = True
                        break
                    if not self.repo.is_date_skipped(series.id, candidate):
                        series.next_occurrence_date = candidate
                        break
                    candidate = calculate_next_occurrence(
                        current_date=candidate,
                        frequency=series.frequency,
                        interval=series.interval,
                        weekdays=parsed_weekdays,
                        day_of_month=series.day_of_month,
                        month_of_year=series.month_of_year,
                    )

        updated = self.repo.update(series, commit=False)

        if changes:
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    recurring_task_id=updated.id,
                    entity_type=ActivityEntityType.RECURRING_TASK.value,
                    entity_id=updated.id,
                    action=ActivityAction.RECURRING_SERIES_UPDATED.value,
                    changes=changes,
                    extra_metadata={"title": updated.title},
                ),
                commit=False,
            )

        self.db.commit()
        return self._to_response(updated)

    def pause_series(self, series_id: uuid.UUID, user_id: uuid.UUID) -> RecurringTaskResponse:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")
        series.is_active = False
        updated = self.repo.update(series, commit=False)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                recurring_task_id=updated.id,
                entity_type=ActivityEntityType.RECURRING_TASK.value,
                entity_id=updated.id,
                action=ActivityAction.RECURRING_SERIES_PAUSED.value,
                changes={"is_active": {"old": True, "new": False}},
                extra_metadata={"title": updated.title},
            ),
            commit=False,
        )

        self.db.commit()
        return self._to_response(updated)

    def resume_series(self, series_id: uuid.UUID, user_id: uuid.UUID) -> RecurringTaskResponse:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")
        if series.is_stopped:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot resume a stopped series.")
        series.is_active = True
        updated = self.repo.update(series, commit=False)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                recurring_task_id=updated.id,
                entity_type=ActivityEntityType.RECURRING_TASK.value,
                entity_id=updated.id,
                action=ActivityAction.RECURRING_SERIES_RESUMED.value,
                changes={"is_active": {"old": False, "new": True}},
                extra_metadata={"title": updated.title},
            ),
            commit=False,
        )

        self.db.commit()
        return self._to_response(updated)

    def stop_series(self, series_id: uuid.UUID, user_id: uuid.UUID) -> RecurringTaskResponse:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")
        series.is_stopped = True
        series.is_active = False
        series.next_occurrence_date = None
        updated = self.repo.update(series, commit=False)

        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                recurring_task_id=updated.id,
                entity_type=ActivityEntityType.RECURRING_TASK.value,
                entity_id=updated.id,
                action=ActivityAction.RECURRING_SERIES_STOPPED.value,
                changes={"is_stopped": {"old": False, "new": True}, "is_active": {"old": True, "new": False}},
                extra_metadata={"title": updated.title},
            ),
            commit=False,
        )

        self.db.commit()
        return self._to_response(updated)

    def delete_series(self, series_id: uuid.UUID, user_id: uuid.UUID) -> None:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")

        # Log deletion snapshot before removing
        self.activity_repo.create(
            ActivityLog(
                user_id=user_id,
                actor_id=user_id,
                recurring_task_id=series.id,
                entity_type=ActivityEntityType.RECURRING_TASK.value,
                entity_id=series.id,
                action=ActivityAction.RECURRING_SERIES_DELETED.value,
                changes=None,
                extra_metadata={
                    "title": series.title,
                    "frequency": series.frequency.value if hasattr(series.frequency, "value") else str(series.frequency),
                },
            ),
            commit=False,
        )

        self.repo.delete(series, commit=True)

    def list_series(
        self,
        user_id: uuid.UUID,
        frequency: Optional[RecurrenceFrequency] = None,
        is_active: Optional[bool] = None,
        is_stopped: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> RecurringTaskListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        items, total = self.repo.list_series(
            user_id=user_id,
            frequency=frequency,
            is_active=is_active,
            is_stopped=is_stopped,
            search=search,
            offset=offset,
            limit=page_size,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return RecurringTaskListResponse(
            items=[self._to_response(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def skip_occurrence(
        self,
        series_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: RecurringTaskSkipRequest,
    ) -> RecurringTaskResponse:
        series = self.repo.get_by_id_for_update(series_id, user_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring task series not found.")

        today = datetime.now(timezone.utc).date()
        if payload.skip_date < today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot skip a past occurrence date.",
            )

        parsed_weekdays = self._parse_weekdays_from_str(series.weekdays)
        is_valid = is_valid_recurrence_date(
            candidate_date=payload.skip_date,
            start_date=series.start_date,
            frequency=series.frequency,
            interval=series.interval,
            weekdays=parsed_weekdays,
            day_of_month=series.day_of_month,
            month_of_year=series.month_of_year,
            end_date=series.end_date,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Date {payload.skip_date} does not belong to the recurrence schedule.",
            )

        # Check if already skipped (idempotent)
        if not self.repo.is_date_skipped(series.id, payload.skip_date):
            skip = RecurringTaskSkip(
                recurring_task_id=series.id,
                user_id=user_id,
                skip_date=payload.skip_date,
                reason=payload.reason,
            )
            self.repo.add_skip(skip, commit=False)

            # Log RECURRING_OCCURRENCE_SKIPPED
            self.activity_repo.create(
                ActivityLog(
                    user_id=user_id,
                    actor_id=user_id,
                    recurring_task_id=series.id,
                    entity_type=ActivityEntityType.RECURRING_TASK.value,
                    entity_id=series.id,
                    action=ActivityAction.RECURRING_OCCURRENCE_SKIPPED.value,
                    changes=None,
                    extra_metadata={
                        "title": series.title,
                        "skip_date": payload.skip_date.isoformat(),
                        "reason": payload.reason,
                    },
                ),
                commit=False,
            )

        # Advance next_occurrence_date if the skipped date matches current next
        if series.next_occurrence_date == payload.skip_date:
            candidate = payload.skip_date
            while True:
                next_date = calculate_next_occurrence(
                    current_date=candidate,
                    frequency=series.frequency,
                    interval=series.interval,
                    weekdays=parsed_weekdays,
                    day_of_month=series.day_of_month,
                    month_of_year=series.month_of_year,
                )
                if series.end_date and next_date > series.end_date:
                    series.next_occurrence_date = None
                    series.is_stopped = True
                    break
                # If next_date is also already skipped, loop forward
                if not self.repo.is_date_skipped(series.id, next_date):
                    series.next_occurrence_date = next_date
                    break
                candidate = next_date

            self.repo.update(series, commit=False)

        self.db.commit()
        return self._to_response(series)

    def list_occurrences(
        self,
        series_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> TaskListResponse:
        # Verify ownership
        self.get_series(series_id, user_id)
        from app.services.task_service import TaskService
        task_service = TaskService(self.db)

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        from sqlalchemy import select, func, desc
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.project),
                selectinload(Task.tags),
                selectinload(Task.subtasks),
            )
            .where(
                Task.recurring_task_id == series_id,
                Task.user_id == user_id,
            )
            .order_by(desc(Task.occurrence_date), desc(Task.id))
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.db.execute(stmt).scalars().all())

        count_stmt = select(func.count(Task.id)).where(
            Task.recurring_task_id == series_id,
            Task.user_id == user_id,
        )
        total = self.db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return TaskListResponse(
            items=[task_service._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _generate_occurrences_for_series(self, locked_series: RecurringTask, cutoff: date) -> int:
        """
        Internal generator for a single series up to cutoff date.
        Flushes created tasks to DB session without committing, leaving transaction ownership to caller.
        """
        if not locked_series.is_active or locked_series.is_stopped:
            return 0

        parsed_weekdays = self._parse_weekdays_from_str(locked_series.weekdays)
        created_count = 0

        while (
            locked_series.next_occurrence_date
            and locked_series.next_occurrence_date <= cutoff
        ):
            curr_date = locked_series.next_occurrence_date

            # Check max occurrences limit
            if (
                locked_series.max_occurrences is not None
                and locked_series.occurrences_generated >= locked_series.max_occurrences
            ):
                locked_series.is_stopped = True
                locked_series.next_occurrence_date = None
                break

            # Check end_date limit
            if locked_series.end_date and curr_date > locked_series.end_date:
                locked_series.is_stopped = True
                locked_series.next_occurrence_date = None
                break

            # Check if this date was skipped
            if not self.repo.is_date_skipped(locked_series.id, curr_date):
                # Check if occurrence already exists (idempotency safety)
                from sqlalchemy import select
                existing_task = self.db.execute(
                    select(Task).where(
                        Task.recurring_task_id == locked_series.id,
                        Task.occurrence_date == curr_date,
                    )
                ).scalar_one_or_none()

                if not existing_task:
                    due_datetime = datetime.combine(curr_date, datetime.min.time(), tzinfo=timezone.utc)
                    occurrence_task = Task(
                        user_id=locked_series.user_id,
                        recurring_task_id=locked_series.id,
                        occurrence_date=curr_date,
                        occurrence_index=locked_series.occurrences_generated + 1,
                        title=locked_series.title,
                        description=locked_series.description,
                        priority=locked_series.priority,
                        status=TaskStatus.TODO,
                        category_id=locked_series.category_id,
                        project_id=locked_series.project_id,
                        start_date=due_datetime,
                        due_date=due_datetime,
                        is_archived=False,
                    )
                    self.db.add(occurrence_task)
                    self.db.flush()  # assign occurrence_task.id
                    locked_series.occurrences_generated += 1
                    created_count += 1

                    # Log RECURRING_OCCURRENCE_GENERATED
                    self.activity_repo.create(
                        ActivityLog(
                            user_id=locked_series.user_id,
                            actor_id=locked_series.user_id,
                            task_id=occurrence_task.id,
                            recurring_task_id=locked_series.id,
                            entity_type=ActivityEntityType.TASK.value,
                            entity_id=occurrence_task.id,
                            action=ActivityAction.RECURRING_OCCURRENCE_GENERATED.value,
                            changes=None,
                            extra_metadata={
                                "title": occurrence_task.title,
                                "occurrence_date": curr_date.isoformat(),
                                "series_title": locked_series.title,
                            },
                        ),
                        commit=False,
                    )

            # Calculate next date
            next_date = calculate_next_occurrence(
                current_date=curr_date,
                frequency=locked_series.frequency,
                interval=locked_series.interval,
                weekdays=parsed_weekdays,
                day_of_month=locked_series.day_of_month,
                month_of_year=locked_series.month_of_year,
            )

            if locked_series.end_date and next_date > locked_series.end_date:
                locked_series.is_stopped = True
                locked_series.next_occurrence_date = None
                break

            if (
                locked_series.max_occurrences is not None
                and locked_series.occurrences_generated >= locked_series.max_occurrences
            ):
                locked_series.is_stopped = True
                locked_series.next_occurrence_date = None
                break

            locked_series.next_occurrence_date = next_date

        self.repo.update(locked_series, commit=False)
        self.db.flush()
        return created_count

    def generate_due_occurrences(
        self,
        user_id: Optional[uuid.UUID] = None,
        target_date: Optional[date] = None,
    ) -> int:
        """
        Idempotent occurrence generator.
        Generates occurrences for active series up to target_date (defaults to current UTC date).
        Returns total count of created tasks.
        """
        cutoff = target_date or datetime.now(timezone.utc).date()
        due_series_list = self.repo.get_due_series_for_generation(cutoff, user_id=user_id)
        total_created = 0

        for series in due_series_list:
            try:
                # Re-fetch with row lock to prevent race conditions across parallel runs
                locked_series = self.repo.get_by_id_for_update(series.id, series.user_id)
                if not locked_series or not locked_series.is_active or locked_series.is_stopped:
                    continue

                created_count = self._generate_occurrences_for_series(locked_series, cutoff=cutoff)
                self.db.commit()
                total_created += created_count
            except Exception:
                self.db.rollback()
                raise

        return total_created

