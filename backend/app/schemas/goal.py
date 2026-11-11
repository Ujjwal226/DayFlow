import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.goal import (
    GoalCategory,
    GoalPriority,
    GoalStatus,
    GoalType,
    PlanningPeriodType,
    ProgressCalculationMethod,
)


# --- Milestone Schemas ---

class MilestoneBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    order_index: int = 0


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_completed: Optional[bool] = None
    order_index: Optional[int] = None


class MilestoneReorderItem(BaseModel):
    id: uuid.UUID
    order_index: int


class MilestoneResponse(MilestoneBase):
    id: uuid.UUID
    goal_id: uuid.UUID
    user_id: uuid.UUID
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Goal Activity Schemas ---

class GoalActivityResponse(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    user_id: uuid.UUID
    action: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Linked Task Summary ---

class LinkedTaskItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    priority: str
    due_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


# --- Goal Schemas ---

class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: GoalCategory = GoalCategory.PERSONAL
    goal_type: GoalType = GoalType.OUTCOME
    priority: GoalPriority = GoalPriority.MEDIUM
    status: GoalStatus = GoalStatus.NOT_STARTED

    progress_method: ProgressCalculationMethod = ProgressCalculationMethod.MANUAL
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)

    start_date: Optional[date] = None
    target_date: Optional[date] = None
    project_id: Optional[uuid.UUID] = None


class GoalCreate(GoalBase):
    linked_task_ids: Optional[List[uuid.UUID]] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[GoalCategory] = None
    goal_type: Optional[GoalType] = None
    priority: Optional[GoalPriority] = None
    status: Optional[GoalStatus] = None

    progress_method: Optional[ProgressCalculationMethod] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)

    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)

    start_date: Optional[date] = None
    target_date: Optional[date] = None
    project_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None


class GoalResponse(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_archived: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    project_name: Optional[str] = None
    milestones: List[MilestoneResponse] = []
    linked_tasks: List[LinkedTaskItem] = []
    milestone_count: int = 0
    completed_milestone_count: int = 0
    linked_task_count: int = 0
    completed_task_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class GoalListResponse(BaseModel):
    items: List[GoalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Task Link / Unlink ---

class TaskLinkPayload(BaseModel):
    task_id: uuid.UUID


# --- Planning Objective Schemas ---

class PlanningObjectiveBase(BaseModel):
    period_type: PlanningPeriodType
    period_date: date
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: GoalPriority = GoalPriority.MEDIUM
    goal_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    order_index: int = 0


class PlanningObjectiveCreate(PlanningObjectiveBase):
    pass


class PlanningObjectiveUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[GoalPriority] = None
    is_completed: Optional[bool] = None
    goal_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    order_index: Optional[int] = None


class PlanningObjectiveResponse(PlanningObjectiveBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    goal_title: Optional[str] = None
    task_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PlanningPeriodSummary(BaseModel):
    period_type: PlanningPeriodType
    period_date: date
    total_objectives: int
    completed_objectives: int
    completion_rate: float
    objectives: List[PlanningObjectiveResponse]


# --- Analytics Schemas ---

class GoalCompletionDateCount(BaseModel):
    date: str
    count: int


class GoalCategoryCount(BaseModel):
    category: str
    count: int
    completed_count: int


class GoalPriorityCount(BaseModel):
    priority: str
    count: int


class GoalStatusCount(BaseModel):
    status: str
    count: int


class GoalAnalyticsOverview(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    at_risk_goals: int
    overdue_goals: int = 0
    completion_rate: float
    average_progress_percentage: float
    average_completion_time_days: float = 0.0
    milestone_completion_rate: float
    linked_task_completion_rate: float
    categories: List[GoalCategoryCount]
    priorities: List[GoalPriorityCount]
    statuses: List[GoalStatusCount]
    recent_completions: List[GoalResponse]
    upcoming_deadlines: List[GoalResponse]
    goals_completed_over_time: List[GoalCompletionDateCount] = []
    daily_planning_completion_rate: float
    weekly_planning_completion_rate: float
    monthly_planning_completion_rate: float = 0.0
