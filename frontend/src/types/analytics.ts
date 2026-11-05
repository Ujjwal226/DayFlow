export interface ProductivityOverviewResponse {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  cancelled_tasks: number;
  completion_rate: number;
  period_start: string;
  period_end: string;
  tasks_created_in_period: number;
  tasks_completed_in_period: number;
  tasks_reopened_in_period: number;
  net_completions_in_period: number;
}

export interface TrendBucket {
  bucket_label: string;
  start_date: string;
  end_date: string;
  created_count: number;
  gross_completions: number;
  reopened_count: number;
  net_completions: number;
  unique_tasks_completed: number;
}

export interface PeriodComparison {
  current_period_completions: number;
  prior_period_completions: number;
  completion_change_percentage: number | null;
  current_period_created: number;
  prior_period_created: number;
  created_change_percentage: number | null;
}

export interface ProductivityTrendsResponse {
  interval: 'daily' | 'weekly' | 'monthly';
  timezone: string;
  period_start: string;
  period_end: string;
  buckets: TrendBucket[];
  comparison: PeriodComparison;
  historical_completeness_note: string;
}

export interface HeatmapCell {
  date: string;
  count: number;
  level: number; // 0 to 4
}

export interface ConsistencyAnalyticsResponse {
  current_streak_days: number;
  longest_streak_days: number;
  most_productive_weekday: string | null;
  weekday_completion_distribution: Record<string, number>;
  timezone: string;
  total_productive_days: number;
  heatmap_365_days: HeatmapCell[];
}

export interface ProjectAnalyticsItem {
  project_id: string;
  project_name: string;
  project_color: string | null;
  project_status: string;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completion_percentage: number;
}

export interface ProjectAnalyticsResponse {
  projects: ProjectAnalyticsItem[];
  total_projects: number;
}

export interface CategoryAnalyticsItem {
  category_id: string | null;
  category_name: string;
  category_color: string | null;
  category_icon: string | null;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  completion_rate: number;
}

export interface CategoryAnalyticsResponse {
  categories: CategoryAnalyticsItem[];
  total_categories: number;
}

export interface WorkloadHorizonBreakdown {
  overdue: number;
  due_today: number;
  due_tomorrow: number;
  due_next_7_days: number;
  due_later: number;
  no_due_date: number;
}

export interface PriorityDistribution {
  urgent: number;
  high: number;
  medium: number;
  low: number;
}

export interface WorkloadAnalyticsResponse {
  total_pending_tasks: number;
  priority_distribution: PriorityDistribution;
  horizons: WorkloadHorizonBreakdown;
  timezone: string;
}

export interface RecurringFrequencyBreakdown {
  daily: number;
  weekly: number;
  monthly: number;
  yearly: number;
  custom: number;
}

export interface RecurringAnalyticsResponse {
  total_series: number;
  active_series: number;
  paused_or_stopped_series: number;
  total_generated_occurrences: number;
  completed_occurrences: number;
  pending_due_occurrences: number;
  future_occurrences: number;
  skipped_occurrences: number;
  eligible_due_occurrences: number;
  adherence_rate: number;
  frequency_breakdown: RecurringFrequencyBreakdown;
  schema_limitations_note: string;
}

export interface AnalyticsTrendsParams {
  interval?: 'daily' | 'weekly' | 'monthly';
  days?: number;
  start_date?: string;
  end_date?: string;
  timezone?: string;
}

export interface AnalyticsOverviewParams {
  start_date?: string;
  end_date?: string;
  days?: number;
}

