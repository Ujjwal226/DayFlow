import { TaskPriority, TaskStatus } from './task';

export interface Subtask {
  id: string;
  user_id: string;
  parent_task_id: string;
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

export interface SubtaskCreatePayload {
  title: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
}

export interface SubtaskUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
}

export interface SubtaskProgress {
  total_subtasks: number;
  completed_subtasks: number;
  remaining_subtasks: number;
  progress_percentage: number;
}

