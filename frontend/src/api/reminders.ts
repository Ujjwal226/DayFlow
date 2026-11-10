import { apiClient } from './client';
import { Reminder, ReminderCreatePayload, ReminderUpdatePayload, ReminderSnoozePayload } from '../types/reminder';

export const getReminders = async (status?: string, taskId?: string): Promise<Reminder[]> => {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  if (taskId) params.task_id = taskId;
  const response = await apiClient.get<Reminder[]>('/api/v1/reminders', { params });
  return response.data;
};

export const getReminder = async (id: string): Promise<Reminder> => {
  const response = await apiClient.get<Reminder>(`/api/v1/reminders/${id}`);
  return response.data;
};

export const createReminder = async (payload: ReminderCreatePayload): Promise<Reminder> => {
  const response = await apiClient.post<Reminder>('/api/v1/reminders', payload);
  return response.data;
};

export const updateReminder = async (id: string, payload: ReminderUpdatePayload): Promise<Reminder> => {
  const response = await apiClient.patch<Reminder>(`/api/v1/reminders/${id}`, payload);
  return response.data;
};

export const snoozeReminder = async (id: string, payload: ReminderSnoozePayload): Promise<Reminder> => {
  const response = await apiClient.post<Reminder>(`/api/v1/reminders/${id}/snooze`, payload);
  return response.data;
};

export const completeReminder = async (id: string): Promise<Reminder> => {
  const response = await apiClient.post<Reminder>(`/api/v1/reminders/${id}/complete`);
  return response.data;
};

export const dismissReminder = async (id: string): Promise<Reminder> => {
  const response = await apiClient.post<Reminder>(`/api/v1/reminders/${id}/dismiss`);
  return response.data;
};

export const deleteReminder = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/reminders/${id}`);
};
