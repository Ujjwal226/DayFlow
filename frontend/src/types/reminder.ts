export interface Reminder {
  id: string;
  user_id: string;
  task_id?: string | null;
  title: string;
  description?: string | null;
  scheduled_at: string;
  timezone: string;
  recurrence: 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  delivery_channels: string;
  status: 'PENDING' | 'SENT' | 'COMPLETED' | 'DISMISSED' | 'SNOOZED';
  snoozed_until?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreatePayload {
  title: string;
  description?: string | null;
  scheduled_at: string;
  timezone?: string;
  recurrence?: 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  delivery_channels?: string;
  task_id?: string | null;
}

export interface ReminderUpdatePayload {
  title?: string;
  description?: string | null;
  scheduled_at?: string;
  timezone?: string;
  recurrence?: 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  delivery_channels?: string;
  task_id?: string | null;
  status?: 'PENDING' | 'SENT' | 'COMPLETED' | 'DISMISSED' | 'SNOOZED';
}

export interface ReminderSnoozePayload {
  snooze_minutes: number;
}

