import { apiClient } from './client';
import {
  Task,
  TaskCreatePayload,
  TaskFilterParams,
  TaskListResponse,
  TaskStatistics,
  TaskUpdatePayload,
} from '../types/task';
import { MessageResponse } from '../types/auth';

export const tasksApi = {
  createTask: async (payload: TaskCreatePayload): Promise<Task> => {
    const response = await apiClient.post<Task>('/api/v1/tasks', payload);
    return response.data;
  },

  listTasks: async (params?: TaskFilterParams): Promise<TaskListResponse> => {
    const response = await apiClient.get<TaskListResponse>('/api/v1/tasks', { params });
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/api/v1/tasks/${taskId}`);
    return response.data;
  },

  updateTask: async (taskId: string, payload: TaskUpdatePayload): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/api/v1/tasks/${taskId}`, payload);
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/tasks/${taskId}`);
    return response.data;
  },

  duplicateTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.post<Task>(`/api/v1/tasks/${taskId}/duplicate`);
    return response.data;
  },

  archiveTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/api/v1/tasks/${taskId}/archive`);
    return response.data;
  },

  restoreTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/api/v1/tasks/${taskId}/restore`);
    return response.data;
  },

  getStatistics: async (): Promise<TaskStatistics> => {
    const response = await apiClient.get<TaskStatistics>('/api/v1/tasks/statistics');
    return response.data;
  },
};
