import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.goal import (
    Goal,
    GoalActivity,
    GoalCategory,
    GoalMilestone,
    GoalPriority,
    GoalStatus,
    PlanningObjective,
    PlanningPeriodType,
    ProgressCalculationMethod,
)
from app.models.project import Project
from app.models.reminder import Notification
from app.models.task import Task
from app.repositories.goal_repository import GoalRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.goal import (
    GoalAnalyticsOverview,
    GoalCategoryCount,
    GoalCreate,
    GoalPriorityCount,
    GoalResponse,
    GoalStatusCount,
    GoalUpdate,
    LinkedTaskItem,
    MilestoneCreate,
    MilestoneReorderItem,
    MilestoneResponse,
    MilestoneUpdate,
    PlanningObjectiveCreate,
    PlanningObjectiveResponse,
    PlanningObjectiveUpdate,
    PlanningPeriodSummary,
)


class GoalService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GoalRepository(db)
        self.notif_repo = NotificationRepository(db)

    # --- Validation Helpers ---

    def _validate_project(self, project_id: Optional[uuid.UUID], user_id: uuid.UUID) -> Optional[Project]:
        if not project_id:
            return None
        project = self.db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated project not found or does not belong to you",
            )
        return project

    def _validate_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated task not found or does not belong to you",
            )
        return task

    # --- Progress Recalculation ---

    def _recalculate_progress(self, goal: Goal) -> None:
        """Calculates progress percentage depending on goal.progress_method."""
        if goal.progress_method == ProgressCalculationMethod.MILESTONE.value:
            milestones = goal.milestones
            if not milestones:
                goal.progress_percentage = 0.0
            else:
                completed = sum(1 for m in milestones if m.is_completed)
                goal.progress_percentage = round((completed / len(milestones)) * 100.0, 1)

        elif goal.progress_method == ProgressCalculationMethod.NUMERIC.value:
            if goal.target_value and goal.target_value > 0:
                current = goal.current_value or 0.0
                goal.progress_percentage = min(100.0, max(0.0, round((current / goal.target_value) * 100.0, 1)))
            else:
                goal.progress_percentage = 0.0

        # Note: If MANUAL, user-entered progress_percentage is preserved!

        # If progress is 100% and status was not CANCELLED or COMPLETED, update status appropriately
        if goal.progress_percentage >= 100.0 and goal.status in [GoalStatus.NOT_STARTED.value, GoalStatus.IN_PROGRESS.value, GoalStatus.ON_TRACK.value, GoalStatus.AT_RISK.value]:
            goal.status = GoalStatus.COMPLETED.value
            if not goal.completed_at:
                goal.completed_at = datetime.now(timezone.utc)
        elif goal.progress_percentage < 100.0 and goal.status == GoalStatus.COMPLETED.value:
            # Reopened if progress dropped below 100%
            goal.status = GoalStatus.IN_PROGRESS.value
            goal.completed_at = None

    def _serialize_goal(self, goal: Goal) -> GoalResponse:
        milestones = [MilestoneResponse.model_validate(m) for m in goal.milestones]
        linked_tasks = []
        for link in goal.task_links:
            if link.task:
                linked_tasks.append(
                    LinkedTaskItem(
                        id=link.task.id,
                        title=link.task.title,
                        status=link.task.status,
                        priority=link.task.priority,
                        due_date=link.task.due_date,
                    )
                )

        completed_milestone_count = sum(1 for m in goal.milestones if m.is_completed)
        completed_task_count = sum(1 for t in linked_tasks if t.status == "COMPLETED")

        return GoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            project_id=goal.project_id,
            title=goal.title,
            description=goal.description,
            category=goal.category,
            goal_type=goal.goal_type,
            priority=goal.priority,
            status=goal.status,
            progress_method=goal.progress_method,
            progress_percentage=goal.progress_percentage,
            target_value=goal.target_value,
            current_value=goal.current_value,
            unit=goal.unit,
            start_date=goal.start_date,
            target_date=goal.target_date,
            completed_at=goal.completed_at,
            is_archived=goal.is_archived,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            project_name=goal.project.name if goal.project else None,
            milestones=milestones,
            linked_tasks=linked_tasks,
            milestone_count=len(goal.milestones),
            completed_milestone_count=completed_milestone_count,
            linked_task_count=len(linked_tasks),
            completed_task_count=completed_task_count,
        )

    # --- Goal CRUD ---

    def create_goal(self, user_id: uuid.UUID, data: GoalCreate) -> GoalResponse:
        self._validate_project(data.project_id, user_id)

        now = datetime.now(timezone.utc)
        completed_at = now if data.status == GoalStatus.COMPLETED else None

        goal = Goal(
            user_id=user_id,
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            category=data.category.value,
            goal_type=data.goal_type.value,
            priority=data.priority.value,
            status=data.status.value,
            progress_method=data.progress_method.value,
            progress_percentage=data.progress_percentage,
            target_value=data.target_value,
            current_value=data.current_value,
            unit=data.unit,
            start_date=data.start_date,
            target_date=data.target_date,
            completed_at=completed_at,
        )

        self._recalculate_progress(goal)
        created = self.repo.create_goal(goal)

        # Link initial tasks if supplied
        if data.linked_task_ids:
            for task_id in data.linked_task_ids:
                self._validate_task(task_id, user_id)
                self.repo.link_task(created.id, task_id)

        self.repo.log_activity(
            goal_id=created.id,
            user_id=user_id,
            action="CREATED",
            description=f"Goal '{created.title}' created",
        )
        self.db.commit()

        # Refresh
        refreshed = self.repo.get_goal_by_id(created.id, user_id)
        return self._serialize_goal(refreshed)

    def get_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> GoalResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return self._serialize_goal(goal)

    def list_goals(
        self,
        user_id: uuid.UUID,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        linked_task_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[GoalResponse], int, int]:
        offset = (page - 1) * page_size
        items, total = self.repo.list_goals(
            user_id=user_id,
            category=category,
            status=status,
            priority=priority,
            project_id=project_id,
            linked_task_id=linked_task_id,
            search=search,
            is_archived=is_archived,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=page_size,
            offset=offset,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return [self._serialize_goal(g) for g in items], total, total_pages

    def update_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID, data: GoalUpdate) -> GoalResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        if data.project_id is not None:
            self._validate_project(data.project_id, user_id)
            goal.project_id = data.project_id

        # Activity logging tracking
        changes = []

        if data.title is not None and data.title != goal.title:
            changes.append(f"Title changed from '{goal.title}' to '{data.title}'")
            goal.title = data.title

        if data.description is not None:
            goal.description = data.description

        if data.category is not None and data.category.value != goal.category:
            changes.append(f"Category changed to {data.category.value}")
            goal.category = data.category.value

        if data.goal_type is not None and data.goal_type.value != goal.goal_type:
            changes.append(f"Type changed to {data.goal_type.value}")
            goal.goal_type = data.goal_type.value

        if data.priority is not None and data.priority.value != goal.priority:
            changes.append(f"Priority changed to {data.priority.value}")
            goal.priority = data.priority.value

        if data.status is not None and data.status.value != goal.status:
            old_s = goal.status
            new_s = data.status.value
            changes.append(f"Status changed from {old_s} to {new_s}")
            goal.status = new_s
            if new_s == GoalStatus.COMPLETED.value:
                goal.completed_at = datetime.now(timezone.utc)
                # Create completion notification
                try:
                    notif = Notification(
                        user_id=user_id,
                        title=f"Goal Completed: {goal.title}",
                        message=f"Congratulations! You completed the goal '{goal.title}'.",
                        type="SYSTEM",
                    )
                    self.notif_repo.create(notif)
                except Exception:
                    pass
            elif old_s == GoalStatus.COMPLETED.value and new_s != GoalStatus.COMPLETED.value:
                goal.completed_at = None

        if data.progress_method is not None:
            goal.progress_method = data.progress_method.value

        if data.progress_percentage is not None:
            goal.progress_percentage = data.progress_percentage

        if data.target_value is not None:
            goal.target_value = data.target_value

        if data.current_value is not None:
            goal.current_value = data.current_value

        if data.unit is not None:
            goal.unit = data.unit

        if data.start_date is not None:
            goal.start_date = data.start_date

        if data.target_date is not None:
            if goal.target_date != data.target_date:
                changes.append(f"Target deadline changed to {data.target_date}")
            goal.target_date = data.target_date

        if data.is_archived is not None:
            goal.is_archived = data.is_archived
            changes.append(f"Goal {'archived' if data.is_archived else 'restored'}")

        self._recalculate_progress(goal)
        self.repo.update_goal(goal)

        for ch in changes:
            self.repo.log_activity(goal_id=goal.id, user_id=user_id, action="UPDATED", description=ch)

        self.db.commit()
        refreshed = self.repo.get_goal_by_id(goal.id, user_id)
        return self._serialize_goal(refreshed)

    def delete_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> None:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        self.repo.delete_goal(goal)
        self.db.commit()

    def complete_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> GoalResponse:
        return self.update_goal(goal_id, user_id, GoalUpdate(status=GoalStatus.COMPLETED, progress_percentage=100.0))

    def reopen_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> GoalResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        # Explicit reopening transition: preserve user-entered progress percentage exactly as it was.
        # Do not silently overwrite to 90% or any arbitrary value.
        goal.status = GoalStatus.IN_PROGRESS.value
        goal.completed_at = None

        # If method is MILESTONE or NUMERIC, recalculate based on underlying state
        if goal.progress_method == ProgressCalculationMethod.MILESTONE.value:
            milestones = goal.milestones
            if milestones:
                completed = sum(1 for m in milestones if m.is_completed)
                goal.progress_percentage = round((completed / len(milestones)) * 100.0, 1)
            else:
                goal.progress_percentage = 0.0
        elif goal.progress_method == ProgressCalculationMethod.NUMERIC.value:
            if goal.target_value and goal.target_value > 0:
                current = goal.current_value or 0.0
                goal.progress_percentage = min(100.0, max(0.0, round((current / goal.target_value) * 100.0, 1)))
            else:
                goal.progress_percentage = 0.0
        # If MANUAL, goal.progress_percentage remains completely untouched.

        self.repo.update_goal(goal)
        self.repo.log_activity(
            goal_id=goal.id,
            user_id=user_id,
            action="REOPENED",
            description=f"Goal reopened from completed state. Progress preserved at {goal.progress_percentage}%.",
        )
        self.db.commit()
        refreshed = self.repo.get_goal_by_id(goal.id, user_id)
        return self._serialize_goal(refreshed)

    # --- Milestones ---

    def create_milestone(
        self, goal_id: uuid.UUID, user_id: uuid.UUID, data: MilestoneCreate
    ) -> MilestoneResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        milestone = GoalMilestone(
            goal_id=goal_id,
            user_id=user_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            order_index=data.order_index,
        )
        created = self.repo.create_milestone(milestone)
        self._recalculate_progress(goal)
        self.repo.log_activity(
            goal_id=goal_id,
            user_id=user_id,
            action="MILESTONE_ADDED",
            description=f"Milestone '{created.title}' added",
        )
        self.db.commit()
        return MilestoneResponse.model_validate(created)

    def update_milestone(
        self, milestone_id: uuid.UUID, user_id: uuid.UUID, data: MilestoneUpdate
    ) -> MilestoneResponse:
        milestone = self.repo.get_milestone_by_id(milestone_id, user_id)
        if not milestone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

        goal = self.repo.get_goal_by_id(milestone.goal_id, user_id)

        if data.title is not None:
            milestone.title = data.title
        if data.description is not None:
            milestone.description = data.description
        if data.due_date is not None:
            milestone.due_date = data.due_date
        if data.order_index is not None:
            milestone.order_index = data.order_index
        if data.is_completed is not None:
            milestone.is_completed = data.is_completed
            milestone.completed_at = datetime.now(timezone.utc) if data.is_completed else None
            self.repo.log_activity(
                goal_id=milestone.goal_id,
                user_id=user_id,
                action="MILESTONE_COMPLETED" if data.is_completed else "MILESTONE_REOPENED",
                description=f"Milestone '{milestone.title}' marked as {'completed' if data.is_completed else 'reopened'}",
            )

        if goal:
            self._recalculate_progress(goal)

        self.repo.update_milestone(milestone)
        self.db.commit()
        return MilestoneResponse.model_validate(milestone)

    def delete_milestone(self, milestone_id: uuid.UUID, user_id: uuid.UUID) -> None:
        milestone = self.repo.get_milestone_by_id(milestone_id, user_id)
        if not milestone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

        goal = self.repo.get_goal_by_id(milestone.goal_id, user_id)
        self.repo.delete_milestone(milestone)
        if goal:
            self._recalculate_progress(goal)
            self.repo.log_activity(
                goal_id=goal.id,
                user_id=user_id,
                action="MILESTONE_DELETED",
                description=f"Milestone '{milestone.title}' deleted",
            )
        self.db.commit()

    def reorder_milestones(
        self, goal_id: uuid.UUID, user_id: uuid.UUID, items: List[MilestoneReorderItem]
    ) -> List[MilestoneResponse]:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        for item in items:
            m = self.repo.get_milestone_by_id(item.id, user_id)
            if m and m.goal_id == goal_id:
                m.order_index = item.order_index
                self.repo.update_milestone(m)

        self.db.commit()
        milestones = self.repo.list_milestones(goal_id, user_id)
        return [MilestoneResponse.model_validate(m) for m in milestones]

    # --- Task Linking ---

    def link_task(self, goal_id: uuid.UUID, user_id: uuid.UUID, task_id: uuid.UUID) -> GoalResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        task = self._validate_task(task_id, user_id)
        self.repo.link_task(goal_id, task_id)

        self.repo.log_activity(
            goal_id=goal_id,
            user_id=user_id,
            action="TASK_LINKED",
            description=f"Task '{task.title}' linked to goal",
        )
        self.db.commit()
        refreshed = self.repo.get_goal_by_id(goal_id, user_id)
        return self._serialize_goal(refreshed)

    def unlink_task(self, goal_id: uuid.UUID, user_id: uuid.UUID, task_id: uuid.UUID) -> GoalResponse:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        task = self._validate_task(task_id, user_id)
        self.repo.unlink_task(goal_id, task_id)

        self.repo.log_activity(
            goal_id=goal_id,
            user_id=user_id,
            action="TASK_UNLINKED",
            description=f"Task '{task.title}' unlinked from goal",
        )
        self.db.commit()
        refreshed = self.repo.get_goal_by_id(goal_id, user_id)
        return self._serialize_goal(refreshed)

    # --- Planning Objectives ---

    def create_objective(
        self, user_id: uuid.UUID, data: PlanningObjectiveCreate
    ) -> PlanningObjectiveResponse:
        if data.goal_id:
            goal = self.repo.get_goal_by_id(data.goal_id, user_id)
            if not goal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if data.task_id:
            self._validate_task(data.task_id, user_id)

        obj = PlanningObjective(
            user_id=user_id,
            goal_id=data.goal_id,
            task_id=data.task_id,
            period_type=data.period_type.value,
            period_date=data.period_date,
            title=data.title,
            description=data.description,
            priority=data.priority.value,
            order_index=data.order_index,
        )
        created = self.repo.create_objective(obj)
        self.db.commit()
        refreshed = self.repo.get_objective_by_id(created.id, user_id)
        return self._serialize_objective(refreshed)

    def update_objective(
        self, objective_id: uuid.UUID, user_id: uuid.UUID, data: PlanningObjectiveUpdate
    ) -> PlanningObjectiveResponse:
        obj = self.repo.get_objective_by_id(objective_id, user_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objective not found")

        if data.goal_id is not None:
            if data.goal_id:
                goal = self.repo.get_goal_by_id(data.goal_id, user_id)
                if not goal:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
            obj.goal_id = data.goal_id

        if data.task_id is not None:
            if data.task_id:
                self._validate_task(data.task_id, user_id)
            obj.task_id = data.task_id

        if data.title is not None:
            obj.title = data.title
        if data.description is not None:
            obj.description = data.description
        if data.priority is not None:
            obj.priority = data.priority.value
        if data.order_index is not None:
            obj.order_index = data.order_index
        if data.is_completed is not None:
            obj.is_completed = data.is_completed
            obj.completed_at = datetime.now(timezone.utc) if data.is_completed else None

        self.repo.update_objective(obj)
        self.db.commit()
        refreshed = self.repo.get_objective_by_id(obj.id, user_id)
        return self._serialize_objective(refreshed)

    def delete_objective(self, objective_id: uuid.UUID, user_id: uuid.UUID) -> None:
        obj = self.repo.get_objective_by_id(objective_id, user_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objective not found")
        self.repo.delete_objective(obj)
        self.db.commit()

    def get_planning_summary(
        self, user_id: uuid.UUID, period_type: str, period_date: date
    ) -> PlanningPeriodSummary:
        objectives = self.repo.list_objectives(user_id, period_type, period_date)
        total = len(objectives)
        completed = sum(1 for o in objectives if o.is_completed)
        rate = round((completed / total) * 100.0, 1) if total > 0 else 0.0

        return PlanningPeriodSummary(
            period_type=PlanningPeriodType(period_type),
            period_date=period_date,
            total_objectives=total,
            completed_objectives=completed,
            completion_rate=rate,
            objectives=[self._serialize_objective(o) for o in objectives],
        )

    def _serialize_objective(self, obj: PlanningObjective) -> PlanningObjectiveResponse:
        return PlanningObjectiveResponse(
            id=obj.id,
            user_id=obj.user_id,
            goal_id=obj.goal_id,
            task_id=obj.task_id,
            period_type=PlanningPeriodType(obj.period_type),
            period_date=obj.period_date,
            title=obj.title,
            description=obj.description,
            priority=GoalPriority(obj.priority),
            is_completed=obj.is_completed,
            completed_at=obj.completed_at,
            order_index=obj.order_index,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            goal_title=obj.goal.title if obj.goal else None,
            task_title=obj.task.title if obj.task else None,
        )

    # --- Analytics & Dashboard ---

    def evaluate_goal_health(
        self,
        goal: Goal,
        as_of_date: Optional[date] = None,
        tz_name: str = "UTC",
    ) -> str:
        """
        Deterministically evaluates goal status/health.
        Returns one of: COMPLETED, CANCELLED, AT_RISK, ON_TRACK, IN_PROGRESS, NOT_STARTED.
        """
        if goal.status == GoalStatus.COMPLETED.value:
            return GoalStatus.COMPLETED.value
        if goal.status == GoalStatus.CANCELLED.value:
            return GoalStatus.CANCELLED.value

        if as_of_date is None:
            try:
                tz = ZoneInfo(tz_name)
                as_of_date = datetime.now(tz).date()
            except Exception:
                as_of_date = date.today()

        # If target_date is in the past, active goal is overdue -> AT_RISK
        if goal.target_date and goal.target_date < as_of_date:
            return GoalStatus.AT_RISK.value

        # If start_date and target_date are both set and target_date is future
        if goal.start_date and goal.target_date and goal.target_date >= as_of_date:
            total_duration = (goal.target_date - goal.start_date).days
            if total_duration > 0 and as_of_date >= goal.start_date:
                elapsed = (as_of_date - goal.start_date).days
                expected_progress = min(100.0, (elapsed / total_duration) * 100.0)
                # If actual progress falls behind expected progress by more than 20%, it is AT_RISK
                if (expected_progress - goal.progress_percentage) > 20.0:
                    return GoalStatus.AT_RISK.value
                return GoalStatus.ON_TRACK.value

        # Approaching deadline within 7 days with low progress (< 50%)
        if goal.target_date and 0 <= (goal.target_date - as_of_date).days <= 7:
            if goal.progress_percentage < 50.0:
                return GoalStatus.AT_RISK.value
            return GoalStatus.ON_TRACK.value

        if goal.progress_percentage > 0.0:
            return GoalStatus.IN_PROGRESS.value

        return GoalStatus.NOT_STARTED.value

    def get_analytics(self, user_id: uuid.UUID, tz_name: str = "UTC") -> GoalAnalyticsOverview:
        goals, total = self.repo.list_goals(user_id=user_id, is_archived=False, limit=1000)

        try:
            tz = ZoneInfo(tz_name)
            today_date = datetime.now(tz).date()
        except Exception:
            today_date = date.today()

        active = [g for g in goals if g.status != GoalStatus.COMPLETED.value and g.status != GoalStatus.CANCELLED.value]
        completed = [g for g in goals if g.status == GoalStatus.COMPLETED.value]

        # Calculate overdue and at-risk accurately
        overdue_goals_list = [g for g in active if g.target_date and g.target_date < today_date]
        at_risk = [
            g for g in active
            if g.status == GoalStatus.AT_RISK.value or (g.target_date and g.target_date < today_date)
        ]

        completion_rate = round((len(completed) / total) * 100.0, 1) if total > 0 else 0.0
        avg_progress = round(sum(g.progress_percentage for g in goals) / total, 1) if total > 0 else 0.0

        # Average completion time in days
        completion_durations = []
        for g in completed:
            if g.completed_at and g.created_at:
                diff_days = (g.completed_at - g.created_at).total_seconds() / 86400.0
                if diff_days >= 0:
                    completion_durations.append(diff_days)
        avg_completion_time = (
            round(sum(completion_durations) / len(completion_durations), 1)
            if completion_durations
            else 0.0
        )

        # Milestones rate
        all_milestones = [m for g in goals for m in g.milestones]
        ms_rate = (
            round((sum(1 for m in all_milestones if m.is_completed) / len(all_milestones)) * 100.0, 1)
            if all_milestones
            else 0.0
        )

        # Linked task rate
        all_tasks = [link.task for g in goals for link in g.task_links if link.task]
        task_rate = (
            round((sum(1 for t in all_tasks if t.status == "COMPLETED") / len(all_tasks)) * 100.0, 1)
            if all_tasks
            else 0.0
        )

        # Categories
        cat_map: dict[str, dict] = {c.value: {"total": 0, "completed": 0} for c in GoalCategory}
        for g in goals:
            cat = g.category
            if cat not in cat_map:
                cat_map[cat] = {"total": 0, "completed": 0}
            cat_map[cat]["total"] += 1
            if g.status == GoalStatus.COMPLETED.value:
                cat_map[cat]["completed"] += 1
        categories = [
            GoalCategoryCount(category=cat, count=info["total"], completed_count=info["completed"])
            for cat, info in cat_map.items()
        ]

        # Priorities
        prio_map: dict[str, int] = {p.value: 0 for p in GoalPriority}
        for g in goals:
            prio_map[g.priority] = prio_map.get(g.priority, 0) + 1
        priorities = [GoalPriorityCount(priority=p, count=c) for p, c in prio_map.items()]

        # Statuses
        status_map: dict[str, int] = {s.value: 0 for s in GoalStatus}
        for g in goals:
            status_map[g.status] = status_map.get(g.status, 0) + 1
        statuses = [GoalStatusCount(status=s, count=c) for s, c in status_map.items()]

        # Recent completions & Upcoming deadlines
        recent_completions = sorted(
            completed, key=lambda x: x.completed_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True
        )[:5]

        upcoming = [g for g in active if g.target_date and g.target_date >= today_date]
        upcoming_deadlines = sorted(upcoming, key=lambda x: x.target_date)[:5]

        # Goals completed over time (grouped by completed_at date formatted YYYY-MM-DD)
        completed_date_counts: dict[str, int] = {}
        for g in completed:
            if g.completed_at:
                try:
                    c_date = g.completed_at.astimezone(ZoneInfo(tz_name)).date().isoformat()
                except Exception:
                    c_date = g.completed_at.date().isoformat()
                completed_date_counts[c_date] = completed_date_counts.get(c_date, 0) + 1

        goals_completed_over_time = [
            GoalCompletionDateCount(date=d, count=c)
            for d, c in sorted(completed_date_counts.items())
        ]

        # Daily/Weekly/Monthly Planning completion rates
        today_objs = self.repo.list_objectives(user_id, PlanningPeriodType.DAILY.value, today_date)
        daily_rate = (
            round((sum(1 for o in today_objs if o.is_completed) / len(today_objs)) * 100.0, 1)
            if today_objs
            else 0.0
        )

        # Weekly planning rate (start of week)
        start_of_week = today_date - timedelta(days=today_date.weekday())
        week_objs = self.repo.list_objectives(user_id, PlanningPeriodType.WEEKLY.value, start_of_week)
        weekly_rate = (
            round((sum(1 for o in week_objs if o.is_completed) / len(week_objs)) * 100.0, 1)
            if week_objs
            else 0.0
        )

        # Monthly planning rate (first of month)
        first_of_month = today_date.replace(day=1)
        month_objs = self.repo.list_objectives(user_id, PlanningPeriodType.MONTHLY.value, first_of_month)
        monthly_rate = (
            round((sum(1 for o in month_objs if o.is_completed) / len(month_objs)) * 100.0, 1)
            if month_objs
            else 0.0
        )

        return GoalAnalyticsOverview(
            total_goals=total,
            active_goals=len(active),
            completed_goals=len(completed),
            at_risk_goals=len(at_risk),
            overdue_goals=len(overdue_goals_list),
            completion_rate=completion_rate,
            average_progress_percentage=avg_progress,
            average_completion_time_days=avg_completion_time,
            milestone_completion_rate=ms_rate,
            linked_task_completion_rate=task_rate,
            categories=categories,
            priorities=priorities,
            statuses=statuses,
            recent_completions=[self._serialize_goal(g) for g in recent_completions],
            upcoming_deadlines=[self._serialize_goal(g) for g in upcoming_deadlines],
            goals_completed_over_time=goals_completed_over_time,
            daily_planning_completion_rate=daily_rate,
            weekly_planning_completion_rate=weekly_rate,
            monthly_planning_completion_rate=monthly_rate,
        )

    # --- Goal Activities ---

    def get_goal_activities(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> List[GoalActivity]:
        goal = self.repo.get_goal_by_id(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return self.repo.get_activities(goal_id, user_id)
