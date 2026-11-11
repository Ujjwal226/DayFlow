export type GoalCategory =
  | 'PERSONAL'
  | 'CAREER'
  | 'LEARNING'
  | 'HEALTH'
  | 'FINANCE'
  | 'PROJECTS'
  | 'OTHER';

export type GoalType = 'OUTCOME' | 'NUMERIC' | 'MILESTONE';

export type GoalStatus =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'ON_TRACK'
  | 'AT_RISK'
  | 'COMPLETED'
  | 'CANCELLED';

export type GoalPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type ProgressCalculationMethod = 'MANUAL' | 'MILESTONE' | 'NUMERIC';

export type PlanningPeriodType = 'DAILY' | 'WEEKLY' | 'MONTHLY';

export interface Milestone {
  id: string;
  goal_id: string;
  user_id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface MilestoneCreatePayload {
  title: string;
  description?: string | null;
  due_date?: string | null;
  order_index?: number;
}

export interface MilestoneUpdatePayload {
  title?: string;
  description?: string | null;
  due_date?: string | null;
  is_completed?: boolean;
  order_index?: number;
}

export interface MilestoneReorderItem {
  id: string;
  order_index: number;
}

export interface LinkedTaskItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  due_date: string | null;
}

export interface GoalActivity {
  id: string;
  goal_id: string;
  user_id: string;
  action: string;
  description: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface Goal {
  id: string;
  user_id: string;
  project_id: string | null;
  project_name?: string | null;
  title: string;
  description: string | null;
  category: GoalCategory;
  goal_type: GoalType;
  priority: GoalPriority;
  status: GoalStatus;
  progress_method: ProgressCalculationMethod;
  progress_percentage: number;
  target_value: number | null;
  current_value: number | null;
  unit: string | null;
  start_date: string | null;
  target_date: string | null;
  completed_at: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  milestones: Milestone[];
  linked_tasks: LinkedTaskItem[];
  milestone_count: number;
  completed_milestone_count: number;
  linked_task_count: number;
  completed_task_count: number;
}

export type GoalResponse = Goal;

export interface GoalCreatePayload {
  title: string;
  description?: string | null;
  category?: GoalCategory;
  goal_type?: GoalType;
  priority?: GoalPriority;
  status?: GoalStatus;
  progress_method?: ProgressCalculationMethod;
  progress_percentage?: number;
  target_value?: number | null;
  current_value?: number | null;
  unit?: string | null;
  start_date?: string | null;
  target_date?: string | null;
  project_id?: string | null;
  linked_task_ids?: string[];
}

export interface GoalUpdatePayload {
  title?: string;
  description?: string | null;
  category?: GoalCategory;
  goal_type?: GoalType;
  priority?: GoalPriority;
  status?: GoalStatus;
  progress_method?: ProgressCalculationMethod;
  progress_percentage?: number;
  target_value?: number | null;
  current_value?: number | null;
  unit?: string | null;
  start_date?: string | null;
  target_date?: string | null;
  project_id?: string | null;
  is_archived?: boolean;
}

export interface GoalListResponse {
  items: Goal[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GoalFilterParams {
  category?: GoalCategory;
  status?: GoalStatus;
  priority?: GoalPriority;
  project_id?: string;
  linked_task_id?: string;
  search?: string;
  is_archived?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'target_date' | 'progress_percentage' | 'title';
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface PlanningObjective {
  id: string;
  user_id: string;
  goal_id: string | null;
  goal_title?: string | null;
  task_id: string | null;
  task_title?: string | null;
  period_type: PlanningPeriodType;
  period_date: string;
  title: string;
  description: string | null;
  priority: GoalPriority;
  is_completed: boolean;
  completed_at: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface PlanningObjectiveCreatePayload {
  period_type: PlanningPeriodType;
  period_date: string;
  title: string;
  description?: string | null;
  priority?: GoalPriority;
  goal_id?: string | null;
  task_id?: string | null;
  order_index?: number;
}

export interface PlanningObjectiveUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: GoalPriority;
  is_completed?: boolean;
  goal_id?: string | null;
  task_id?: string | null;
  order_index?: number;
}

export interface PlanningPeriodSummary {
  period_type: PlanningPeriodType;
  period_date: string;
  total_objectives: number;
  completed_objectives: number;
  completion_rate: number;
  objectives: PlanningObjective[];
}

export interface GoalCategoryCount {
  category: string;
  count: number;
  completed_count: number;
}

export interface GoalPriorityCount {
  priority: string;
  count: number;
}

export interface GoalStatusCount {
  status: string;
  count: number;
}

export interface GoalAnalyticsOverview {
  total_goals: int_or_number;
  active_goals: number;
  completed_goals: number;
  at_risk_goals: number;
  completion_rate: number;
  average_progress_percentage: number;
  milestone_completion_rate: number;
  linked_task_completion_rate: number;
  categories: GoalCategoryCount[];
  priorities: GoalPriorityCount[];
  statuses: GoalStatusCount[];
  recent_completions: Goal[];
  upcoming_deadlines: Goal[];
  daily_planning_completion_rate: number;
  weekly_planning_completion_rate: number;
}

type int_or_number = number;
