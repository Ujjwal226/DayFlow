import { Category } from './category';
import { TaskPriority } from './task';

export type RecurrenceFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY' | 'CUSTOM';

export interface RecurringTask {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  category_id: string | null;
  category?: Category | null;
  project_id?: string | null;

  frequency: RecurrenceFrequency;
  interval: number;
  start_date: string;
  end_date: string | null;
  max_occurrences: number | null;

  weekdays: number[] | null;
  day_of_month: number | null;
  month_of_year: number | null;
  timezone: string | null;

  next_occurrence_date: string | null;
  occurrences_generated: number;
  is_active: boolean;
  is_stopped: boolean;

  created_at: string;
  updated_at: string;
}

export interface RecurringTaskCreatePayload {
  title: string;
  description?: string | null;
  priority?: TaskPriority;
  category_id?: string | null;
  project_id?: string | null;

  frequency: RecurrenceFrequency;
  interval?: number;
  start_date: string;
  end_date?: string | null;
  max_occurrences?: number | null;

  weekdays?: number[] | null;
  day_of_month?: number | null;
  month_of_year?: number | null;
  timezone?: string | null;
}

export interface RecurringTaskUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  category_id?: string | null;
  project_id?: string | null;

  frequency?: RecurrenceFrequency;
  interval?: number;
  end_date?: string | null;
  max_occurrences?: number | null;

  weekdays?: number[] | null;
  day_of_month?: number | null;
  month_of_year?: number | null;
}

export interface RecurringTaskSkipPayload {
  skip_date: string;
  reason?: string | null;
}

export interface RecurringTaskListResponse {
  items: RecurringTask[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RecurringTaskFilterParams {
  frequency?: RecurrenceFrequency;
  is_active?: boolean;
  is_stopped?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

