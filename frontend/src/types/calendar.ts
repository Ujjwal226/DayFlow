export type CalendarItemType = 'event' | 'task_deadline';

export type CalendarViewMode = 'month' | 'week' | 'day';

export interface CalendarLinkedTaskSummary {
  id: string;
  title: string;
  status: 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  due_date?: string | null;
}

export interface CalendarEventItem {
  id: string;
  type: 'event';
  title: string;
  description?: string | null;
  location?: string | null;
  color?: string | null;
  is_all_day: boolean;
  timezone: string;
  start_at?: string | null;
  end_at?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  task_id?: string | null;
  task?: CalendarLinkedTaskSummary | null;
  created_at: string;
  updated_at: string;
}

export interface CalendarTaskDeadlineItem {
  id: string;
  type: 'task_deadline';
  title: string;
  description?: string | null;
  status: 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  start_date?: string | null;
  due_date: string;
  project_id?: string | null;
  project?: {
    id: string;
    name: string;
    color?: string | null;
    status: string;
  } | null;
  category_id?: string | null;
  category?: {
    id: string;
    name: string;
    color: string;
    icon?: string | null;
  } | null;
  recurring_task_id?: string | null;
  occurrence_date?: string | null;
  occurrence_index?: number | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export type CalendarFeedItem = CalendarEventItem | CalendarTaskDeadlineItem;

export interface CalendarFeedResponse {
  items: CalendarFeedItem[];
  range_start: string;
  range_end: string;
  timezone: string;
  total: number;
}

export interface CalendarFeedQuery {
  start: string;
  end: string;
  timezone?: string;
  include_tasks?: boolean;
  include_events?: boolean;
  project_id?: string;
  category_id?: string;
  status?: 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  recurring_only?: boolean;
}

export interface CalendarEventCreatePayload {
  title: string;
  description?: string | null;
  location?: string | null;
  color?: string | null;
  is_all_day: boolean;
  timezone?: string;
  start_at?: string | null;
  end_at?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  task_id?: string | null;
}

export interface CalendarEventUpdatePayload {
  title?: string;
  description?: string | null;
  location?: string | null;
  color?: string | null;
  is_all_day?: boolean;
  timezone?: string;
  start_at?: string | null;
  end_at?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  task_id?: string | null;
}

export interface ScheduleTaskPayload {
  task_id: string;
  start_at: string;
  end_at: string;
  timezone?: string;
  title?: string | null;
  description?: string | null;
  color?: string | null;
  location?: string | null;
}

export interface CalendarDateRange {
  start: Date;
  end: Date;
}
