import { apiClient } from './client';
import {
  RecurringTask,
  RecurringTaskCreatePayload,
  RecurringTaskUpdatePayload,
  RecurringTaskSkipPayload,
  RecurringTaskListResponse,
  RecurringTaskFilterParams,
} from '../types/recurringTask';
import { TaskListResponse } from '../types/task';

export const recurringTasksApi = {
  create: async (payload: RecurringTaskCreatePayload): Promise<RecurringTask> => {
    const response = await apiClient.post<RecurringTask>('/api/v1/recurring-tasks', payload);
    return response.data;
  },

  list: async (params?: RecurringTaskFilterParams): Promise<RecurringTaskListResponse> => {
    const response = await apiClient.get<RecurringTaskListResponse>('/api/v1/recurring-tasks', {
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<RecurringTask> => {
    const response = await apiClient.get<RecurringTask>(`/api/v1/recurring-tasks/${id}`);
    return response.data;
  },

  update: async (id: string, payload: RecurringTaskUpdatePayload): Promise<RecurringTask> => {
    const response = await apiClient.patch<RecurringTask>(`/api/v1/recurring-tasks/${id}`, payload);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/recurring-tasks/${id}`);
  },

  pause: async (id: string): Promise<RecurringTask> => {
    const response = await apiClient.post<RecurringTask>(`/api/v1/recurring-tasks/${id}/pause`);
    return response.data;
  },

  resume: async (id: string): Promise<RecurringTask> => {
    const response = await apiClient.post<RecurringTask>(`/api/v1/recurring-tasks/${id}/resume`);
    return response.data;
  },

  stop: async (id: string): Promise<RecurringTask> => {
    const response = await apiClient.post<RecurringTask>(`/api/v1/recurring-tasks/${id}/stop`);
    return response.data;
  },

  listOccurrences: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<TaskListResponse> => {
    const response = await apiClient.get<TaskListResponse>(
      `/api/v1/recurring-tasks/${id}/occurrences`,
      { params }
    );
    return response.data;
  },

  skipOccurrence: async (
    id: string,
    payload: RecurringTaskSkipPayload
  ): Promise<RecurringTask> => {
    const response = await apiClient.post<RecurringTask>(
      `/api/v1/recurring-tasks/${id}/skip`,
      payload
    );
    return response.data;
  },

  triggerGeneration: async (
    targetDate?: string
  ): Promise<{ status: string; created_occurrences: number }> => {
    const response = await apiClient.post<{ status: string; created_occurrences: number }>(
      '/api/v1/recurring-tasks/trigger-generation',
      null,
      { params: targetDate ? { target_date: targetDate } : undefined }
    );
    return response.data;
  },
};
