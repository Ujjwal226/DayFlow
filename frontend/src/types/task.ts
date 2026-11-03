export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  is_archived: boolean;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskCreatePayload {
  title: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  start_date?: string | null;
  due_date?: string | null;
}

export interface TaskUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  start_date?: string | null;
  due_date?: string | null;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskStatistics {
  total: number;
  todo: number;
  in_progress: number;
  completed: number;
  cancelled: number;
  overdue: number;
  upcoming: number;
}

export interface TaskFilterParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date_from?: string;
  due_date_to?: string;
  is_archived?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'due_date' | 'priority' | 'status' | 'title';
  sort_order?: 'asc' | 'desc';
}

