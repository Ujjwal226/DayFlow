export type ActivityEntityType =
  | 'TASK'
  | 'SUBTASK'
  | 'PROJECT'
  | 'RECURRING_TASK'
  | 'CATEGORY'
  | 'TAG';

export type ActivityAction =
  | 'TASK_CREATED'
  | 'TASK_UPDATED'
  | 'TASK_DELETED'
  | 'TASK_COMPLETED'
  | 'TASK_REOPENED'
  | 'TASK_ARCHIVED'
  | 'TASK_RESTORED'
  | 'TASK_DUPLICATED'
  | 'SUBTASK_CREATED'
  | 'SUBTASK_UPDATED'
  | 'SUBTASK_COMPLETED'
  | 'SUBTASK_DELETED'
  | 'PROJECT_CREATED'
  | 'PROJECT_UPDATED'
  | 'PROJECT_ARCHIVED'
  | 'PROJECT_RESTORED'
  | 'PROJECT_DELETED'
  | 'RECURRING_SERIES_CREATED'
  | 'RECURRING_SERIES_UPDATED'
  | 'RECURRING_SERIES_PAUSED'
  | 'RECURRING_SERIES_RESUMED'
  | 'RECURRING_SERIES_STOPPED'
  | 'RECURRING_SERIES_DELETED'
  | 'RECURRING_OCCURRENCE_GENERATED'
  | 'RECURRING_OCCURRENCE_SKIPPED'
  | 'CATEGORY_CREATED'
  | 'CATEGORY_UPDATED'
  | 'CATEGORY_DELETED'
  | 'TAG_CREATED'
  | 'TAG_UPDATED'
  | 'TAG_DELETED'
  | 'TAG_ASSIGNED'
  | 'TAG_REMOVED';

export interface ActivityChangeValue {
  old?: unknown;
  new?: unknown;
}

export interface ActivityLog {
  id: string;
  user_id: string;
  actor_id?: string | null;
  task_id?: string | null;
  recurring_task_id?: string | null;
  entity_type: ActivityEntityType;
  entity_id: string;
  action: ActivityAction;
  changes?: Record<string, ActivityChangeValue> | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface ActivityLogListResponse {
  items: ActivityLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ActivityLogQueryParams {
  action?: string;
  entity_type?: string;
  task_id?: string;
  recurring_task_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

