export interface Notification {
  id: string;
  user_id: string;
  reminder_id?: string | null;
  task_id?: string | null;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  task_reminders_enabled: boolean;
  due_date_reminders_enabled: boolean;
  overdue_reminders_enabled: boolean;
  preferred_timezone: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  updated_at: string;
}

export interface NotificationPreferenceUpdate {
  in_app_enabled?: boolean;
  email_enabled?: boolean;
  task_reminders_enabled?: boolean;
  due_date_reminders_enabled?: boolean;
  overdue_reminders_enabled?: boolean;
  preferred_timezone?: string;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
}

