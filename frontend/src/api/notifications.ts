import { apiClient } from './client';
import { Notification, UnreadCountResponse, NotificationPreference, NotificationPreferenceUpdate } from '../types/notification';

export const getNotifications = async (isRead?: boolean, limit: number = 50, offset: number = 0): Promise<Notification[]> => {
  const params: Record<string, string | number | boolean> = { limit, offset };
  if (isRead !== undefined) {
    params.is_read = isRead;
  }
  const response = await apiClient.get<Notification[]>('/api/v1/notifications', { params });
  return response.data;
};

export const getUnreadNotificationCount = async (): Promise<number> => {
  const response = await apiClient.get<UnreadCountResponse>('/api/v1/notifications/unread-count');
  return response.data.unread_count;
};

export const markNotificationAsRead = async (id: string): Promise<Notification> => {
  const response = await apiClient.patch<Notification>(`/api/v1/notifications/${id}/read`);
  return response.data;
};

export const markAllNotificationsAsRead = async (): Promise<{ message: string; updated_count: number }> => {
  const response = await apiClient.post<{ message: string; updated_count: number }>('/api/v1/notifications/mark-all-read');
  return response.data;
};

export const deleteNotification = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/notifications/${id}`);
};

export const getNotificationPreferences = async (): Promise<NotificationPreference> => {
  const response = await apiClient.get<NotificationPreference>('/api/v1/notification-preferences');
  return response.data;
};

export const updateNotificationPreferences = async (
  payload: NotificationPreferenceUpdate
): Promise<NotificationPreference> => {
  const response = await apiClient.patch<NotificationPreference>('/api/v1/notification-preferences', payload);
  return response.data;
};
