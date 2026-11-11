import math
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.goal import (
    Goal,
    GoalActivity,
    GoalCategory,
    GoalMilestone,
    GoalPriority,
    GoalStatus,
    GoalTaskLink,
    PlanningObjective,
    PlanningPeriodType,
    ProgressCalculationMethod,
)
from app.models.task import Task


class GoalRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Goals ---

    def create_goal(self, goal: Goal) -> Goal:
        self.db.add(goal)
        self.db.flush()
        return goal

    def get_goal_by_id(
        self, goal_id: uuid.UUID, user_id: uuid.UUID, include_archived: bool = True
    ) -> Optional[Goal]:
        query = (
            select(Goal)
            .options(
                selectinload(Goal.milestones),
                selectinload(Goal.task_links).joinedload(GoalTaskLink.task),
                joinedload(Goal.project),
            )
            .where(and_(Goal.id == goal_id, Goal.user_id == user_id))
        )
        if not include_archived:
            query = query.where(Goal.is_archived.is_(False))
        return self.db.scalars(query).first()

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
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Goal], int]:
        query = select(Goal).where(and_(Goal.user_id == user_id, Goal.is_archived == is_archived))

        if category:
            query = query.where(Goal.category == category)
        if status:
            query = query.where(Goal.status == status)
        if priority:
            query = query.where(Goal.priority == priority)
        if project_id:
            query = query.where(Goal.project_id == project_id)
        if linked_task_id:
            query = query.join(GoalTaskLink).where(GoalTaskLink.task_id == linked_task_id)
        if search:
            query = query.where(
                or_(
                    Goal.title.ilike(f"%{search}%"),
                    Goal.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Sorting
        sort_col = getattr(Goal, sort_by, Goal.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        query = (
            query.options(
                selectinload(Goal.milestones),
                selectinload(Goal.task_links).joinedload(GoalTaskLink.task),
                joinedload(Goal.project),
            )
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.scalars(query).all())
        return items, total

    def update_goal(self, goal: Goal) -> Goal:
        self.db.flush()
        return goal

    def delete_goal(self, goal: Goal) -> None:
        self.db.delete(goal)
        self.db.flush()

    # --- Milestones ---

    def create_milestone(self, milestone: GoalMilestone) -> GoalMilestone:
        self.db.add(milestone)
        self.db.flush()
        return milestone

    def get_milestone_by_id(
        self, milestone_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[GoalMilestone]:
        query = select(GoalMilestone).where(
            and_(GoalMilestone.id == milestone_id, GoalMilestone.user_id == user_id)
        )
        return self.db.scalars(query).first()

    def list_milestones(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> List[GoalMilestone]:
        query = (
            select(GoalMilestone)
            .where(and_(GoalMilestone.goal_id == goal_id, GoalMilestone.user_id == user_id))
            .order_by(GoalMilestone.order_index.asc(), GoalMilestone.created_at.asc())
        )
        return list(self.db.scalars(query).all())

    def update_milestone(self, milestone: GoalMilestone) -> GoalMilestone:
        self.db.flush()
        return milestone

    def delete_milestone(self, milestone: GoalMilestone) -> None:
        self.db.delete(milestone)
        self.db.flush()

    # --- Task Links ---

    def link_task(self, goal_id: uuid.UUID, task_id: uuid.UUID) -> GoalTaskLink:
        existing = self.db.scalars(
            select(GoalTaskLink).where(
                and_(GoalTaskLink.goal_id == goal_id, GoalTaskLink.task_id == task_id)
            )
        ).first()
        if existing:
            return existing

        link = GoalTaskLink(goal_id=goal_id, task_id=task_id)
        self.db.add(link)
        self.db.flush()
        return link

    def unlink_task(self, goal_id: uuid.UUID, task_id: uuid.UUID) -> bool:
        link = self.db.scalars(
            select(GoalTaskLink).where(
                and_(GoalTaskLink.goal_id == goal_id, GoalTaskLink.task_id == task_id)
            )
        ).first()
        if link:
            self.db.delete(link)
            self.db.flush()
            return True
        return False

    def get_linked_tasks(self, goal_id: uuid.UUID) -> List[Task]:
        query = (
            select(Task)
            .join(GoalTaskLink, GoalTaskLink.task_id == Task.id)
            .where(GoalTaskLink.goal_id == goal_id)
        )
        return list(self.db.scalars(query).all())

    # --- Planning Objectives ---

    def create_objective(self, obj: PlanningObjective) -> PlanningObjective:
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_objective_by_id(
        self, objective_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[PlanningObjective]:
        query = (
            select(PlanningObjective)
            .options(joinedload(PlanningObjective.goal), joinedload(PlanningObjective.task))
            .where(and_(PlanningObjective.id == objective_id, PlanningObjective.user_id == user_id))
        )
        return self.db.scalars(query).first()

    def list_objectives(
        self,
        user_id: uuid.UUID,
        period_type: str,
        period_date: date,
    ) -> List[PlanningObjective]:
        query = (
            select(PlanningObjective)
            .options(joinedload(PlanningObjective.goal), joinedload(PlanningObjective.task))
            .where(
                and_(
                    PlanningObjective.user_id == user_id,
                    PlanningObjective.period_type == period_type,
                    PlanningObjective.period_date == period_date,
                )
            )
            .order_by(PlanningObjective.order_index.asc(), PlanningObjective.created_at.asc())
        )
        return list(self.db.scalars(query).all())

    def update_objective(self, obj: PlanningObjective) -> PlanningObjective:
        self.db.flush()
        return obj

    def delete_objective(self, obj: PlanningObjective) -> None:
        self.db.delete(obj)
        self.db.flush()

    # --- Goal Activities ---

    def log_activity(
        self,
        goal_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        description: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> GoalActivity:
        act = GoalActivity(
            goal_id=goal_id,
            user_id=user_id,
            action=action,
            description=description,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(act)
        self.db.flush()
        return act

    def get_activities(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> List[GoalActivity]:
        query = (
            select(GoalActivity)
            .where(and_(GoalActivity.goal_id == goal_id, GoalActivity.user_id == user_id))
            .order_by(GoalActivity.created_at.desc())
            .limit(100)
        )
        return list(self.db.scalars(query).all())
