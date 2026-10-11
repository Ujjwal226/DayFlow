/**
 * DayFlow API types – mirrors the Pydantic schemas in backend/app/schemas.py
 * Field names, enum values and response shapes must stay in sync with the backend.
 */

// ─── Enums (exact values from the backend) ───────────────────────────────────

export type Priority = 'low' | 'medium' | 'high';
export type Category = 'work' | 'personal' | 'learning' | 'health' | 'other';
export type TaskStatus = 'pending' | 'completed';
export type EventType = 'created' | 'updated' | 'completed' | 'reopened' | 'deleted' | 'rescheduled';

// ─── Task ─────────────────────────────────────────────────────────────────────

/** Mirrors TaskResponse from schemas.py */
export interface Task {
  id: number;
  title: string;
  description: string | null;
  /** ISO date string, e.g. "2026-10-15" */
  scheduled_date: string;
  /** "HH:MM:SS" or null */
  start_time: string | null;
  /** "HH:MM:SS" or null */
  end_time: string | null;
  priority: Priority;
  category: Category;
  status: TaskStatus;
  /** ISO-8601 UTC datetime */
  created_at: string;
  /** ISO-8601 UTC datetime */
  updated_at: string;
  completed_at: string | null;
  deleted_at: string | null;
  original_scheduled_date: string | null;
}

/** Mirrors TaskCreate – required: title, scheduled_date */
export interface TaskCreate {
  title: string;
  description?: string | null;
  scheduled_date: string;
  start_time?: string | null;
  end_time?: string | null;
  priority?: Priority;
  category?: Category;
}

/** Mirrors TaskUpdate – all fields optional */
export interface TaskUpdate {
  title?: string;
  description?: string | null;
  scheduled_date?: string;
  start_time?: string | null;
  end_time?: string | null;
  priority?: Priority;
  category?: Category;
  status?: TaskStatus;
}

/** Mirrors TaskReschedule */
export interface TaskReschedule {
  scheduled_date: string;
  start_time?: string | null;
  end_time?: string | null;
}

/** Mirrors TaskEventResponse */
export interface TaskEvent {
  id: number;
  task_id: number;
  event_type: EventType;
  /** ISO-8601 UTC datetime */
  event_timestamp: string;
  details?: Record<string, unknown> | null;
}

// ─── Response wrappers ────────────────────────────────────────────────────────

/** Mirrors TaskListResponse */
export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

/** Mirrors MessageResponse */
export interface MessageResponse {
  message: string;
  task_id?: number | null;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ─── Query params for GET /tasks ─────────────────────────────────────────────

export interface TaskFilters {
  status?: TaskStatus;
  category?: Category;
  priority?: Priority;
  skip?: number;
  limit?: number;
}
