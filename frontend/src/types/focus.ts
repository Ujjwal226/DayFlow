export type FocusSessionType = 'FOCUS' | 'SHORT_BREAK' | 'LONG_BREAK';
export type FocusSessionStatus = 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ABANDONED';

export interface FocusSession {
  id: string;
  user_id: string;
  task_id: string | null;
  project_id: string | null;
  session_type: FocusSessionType;
  status: FocusSessionStatus;
  planned_duration_seconds: number;
  actual_duration_seconds: number;
  accumulated_pause_seconds: number;
  started_at: string;
  paused_at: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  task_title?: string | null;
  project_name?: string | null;
}

export interface FocusSessionActiveResponse {
  session: FocusSession;
  server_time: string;
  elapsed_seconds: number;
  remaining_seconds: number;
  is_expired: boolean;
}

export interface FocusSessionStartPayload {
  session_type?: FocusSessionType;
  planned_duration_seconds?: number;
  task_id?: string | null;
  project_id?: string | null;
  notes?: string | null;
}

export interface FocusPreference {
  id: string;
  user_id: string;
  focus_duration_minutes: number;
  short_break_duration_minutes: number;
  long_break_duration_minutes: number;
  long_break_interval: number;
  auto_start_breaks: boolean;
  auto_start_focus: boolean;
  sound_enabled: boolean;
  browser_notifications_enabled: boolean;
  daily_goal_minutes: number;
  created_at?: string;
  updated_at: string;
}

export interface FocusPreferenceUpdatePayload {
  focus_duration_minutes?: number;
  short_break_duration_minutes?: number;
  long_break_duration_minutes?: number;
  long_break_interval?: number;
  auto_start_breaks?: boolean;
  auto_start_focus?: boolean;
  sound_enabled?: boolean;
  browser_notifications_enabled?: boolean;
  daily_goal_minutes?: number;
}

export interface FocusDailySummary {
  today_focus_seconds: number;
  today_completed_sessions: number;
  daily_goal_minutes: number;
  goal_completion_percentage: number;
  streak_days: number;
}

export interface FocusTrendDay {
  date: string;
  focus_minutes: number;
  completed_sessions: number;
}

export interface FocusWeeklyTrends {
  total_focus_minutes: number;
  total_completed_sessions: number;
  average_session_minutes: number;
  days: FocusTrendDay[];
}

export interface FocusTaskBreakdownItem {
  task_id: string | null;
  task_title: string;
  total_focus_minutes: number;
  completed_sessions: number;
}

export interface FocusProjectBreakdownItem {
  project_id: string | null;
  project_name: string;
  total_focus_minutes: number;
  completed_sessions: number;
}

export interface FocusAnalyticsOverview {
  daily: FocusDailySummary;
  weekly: FocusWeeklyTrends;
  task_breakdown: FocusTaskBreakdownItem[];
  project_breakdown: FocusProjectBreakdownItem[];
}
