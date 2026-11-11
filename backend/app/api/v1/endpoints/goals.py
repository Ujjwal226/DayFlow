import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.goal import (
    GoalActivityResponse,
    GoalAnalyticsOverview,
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    GoalUpdate,
    MilestoneCreate,
    MilestoneReorderItem,
    MilestoneResponse,
    MilestoneUpdate,
    PlanningObjectiveCreate,
    PlanningObjectiveResponse,
    PlanningObjectiveUpdate,
    PlanningPeriodSummary,
    TaskLinkPayload,
)
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals & Planning"])


# --- Goals Endpoints ---

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new personal goal with optional milestones, numeric targets, and linked tasks."""
    service = GoalService(db)
    return service.create_goal(current_user.id, data)


@router.get("", response_model=GoalListResponse)
def list_goals(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    linked_task_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    is_archived: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search, filter, and paginate user goals."""
    service = GoalService(db)
    items, total, total_pages = service.list_goals(
        user_id=current_user.id,
        category=category,
        status=status,
        priority=priority,
        project_id=project_id,
        linked_task_id=linked_task_id,
        search=search,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return GoalListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/analytics", response_model=GoalAnalyticsOverview)
def get_goal_analytics(
    tz: str = Query("UTC", description="User preferred timezone name (e.g. America/New_York)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregated goal and planning analytics."""
    service = GoalService(db)
    return service.get_analytics(current_user.id, tz_name=tz)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single goal detail with milestones and linked tasks."""
    service = GoalService(db)
    return service.get_goal(goal_id, current_user.id)


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update goal fields, progress, status, or archive state."""
    service = GoalService(db)
    return service.update_goal(goal_id, current_user.id, data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a goal."""
    service = GoalService(db)
    service.delete_goal(goal_id, current_user.id)


@router.post("/{goal_id}/complete", response_model=GoalResponse)
def complete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark goal as completed with 100% progress."""
    service = GoalService(db)
    return service.complete_goal(goal_id, current_user.id)


@router.post("/{goal_id}/reopen", response_model=GoalResponse)
def reopen_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reopen a completed goal."""
    service = GoalService(db)
    return service.reopen_goal(goal_id, current_user.id)


@router.get("/{goal_id}/activities", response_model=List[GoalActivityResponse])
def get_goal_activities(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get audit activity log for this goal."""
    service = GoalService(db)
    acts = service.get_goal_activities(goal_id, current_user.id)
    return [GoalActivityResponse.model_validate(a) for a in acts]


# --- Milestones Endpoints ---

@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(
    goal_id: uuid.UUID,
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a milestone to a goal."""
    service = GoalService(db)
    return service.create_milestone(goal_id, current_user.id, data)


@router.patch("/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    milestone_id: uuid.UUID,
    data: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update milestone details or completion status."""
    service = GoalService(db)
    return service.update_milestone(milestone_id, current_user.id, data)


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a milestone from a goal."""
    service = GoalService(db)
    service.delete_milestone(milestone_id, current_user.id)


@router.post("/{goal_id}/milestones/reorder", response_model=List[MilestoneResponse])
def reorder_milestones(
    goal_id: uuid.UUID,
    items: List[MilestoneReorderItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reorder milestones within a goal."""
    service = GoalService(db)
    return service.reorder_milestones(goal_id, current_user.id, items)


# --- Task Relationships Endpoints ---

@router.post("/{goal_id}/tasks", response_model=GoalResponse)
def link_task_to_goal(
    goal_id: uuid.UUID,
    payload: TaskLinkPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link an existing task to this goal."""
    service = GoalService(db)
    return service.link_task(goal_id, current_user.id, payload.task_id)


@router.delete("/{goal_id}/tasks/{task_id}", response_model=GoalResponse)
def unlink_task_from_goal(
    goal_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unlink a task from this goal."""
    service = GoalService(db)
    return service.unlink_task(goal_id, current_user.id, task_id)


# --- Daily, Weekly & Monthly Planning Endpoints ---

@router.post("/planning/objectives", response_model=PlanningObjectiveResponse, status_code=status.HTTP_201_CREATED)
def create_planning_objective(
    data: PlanningObjectiveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a daily, weekly, or monthly planning objective."""
    service = GoalService(db)
    return service.create_objective(current_user.id, data)


@router.get("/planning/summary", response_model=PlanningPeriodSummary)
def get_planning_summary(
    period_type: str = Query("DAILY", description="DAILY, WEEKLY, or MONTHLY"),
    period_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get planning period objectives and completion rate for a specific date."""
    service = GoalService(db)
    return service.get_planning_summary(current_user.id, period_type, period_date)


@router.patch("/planning/objectives/{objective_id}", response_model=PlanningObjectiveResponse)
def update_planning_objective(
    objective_id: uuid.UUID,
    data: PlanningObjectiveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a planning objective's title, priority, or completion state."""
    service = GoalService(db)
    return service.update_objective(objective_id, current_user.id, data)


@router.delete("/planning/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_planning_objective(
    objective_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a planning objective."""
    service = GoalService(db)
    service.delete_objective(objective_id, current_user.id)
