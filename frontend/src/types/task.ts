import { Category } from './category';
import { Tag } from './tag';
import { Subtask, SubtaskProgress } from './subtask';

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface Task {
  id: string;
  user_id: string;
  parent_task_id: string | null;
  category_id: string | null;
  category?: Category | null;
  project_id?: string | null;
  tags?: Tag[];
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  is_archived: boolean;
  is_overdue: boolean;
  progress?: SubtaskProgress;
  subtasks?: Subtask[];
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
  category_id?: string | null;
  project_id?: string | null;
  tag_ids?: string[];
}

export interface TaskUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  start_date?: string | null;
  due_date?: string | null;
  category_id?: string | null;
  project_id?: string | null;
  tag_ids?: string[];
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
  category_id?: string;
  project_id?: string;
  tag_id?: string;
  due_date_from?: string;
  due_date_to?: string;
  is_archived?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'due_date' | 'priority' | 'status' | 'title';
  sort_order?: 'asc' | 'desc';
}
