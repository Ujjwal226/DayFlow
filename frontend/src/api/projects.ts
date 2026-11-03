import { apiClient } from './client';
import {
  Project,
  ProjectCreatePayload,
  ProjectListResponse,
  ProjectPriority,
  ProjectStatistics,
  ProjectStatus,
  ProjectUpdatePayload,
} from '../types/project';
import { Task, TaskListResponse, TaskPriority, TaskStatus } from '../types/task';

export interface ProjectFilterParams {
  search?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
  is_archived?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface ProjectTaskFilterParams {
  search?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export const projectsApi = {
  list: async (params?: ProjectFilterParams): Promise<ProjectListResponse> => {
    const res = await apiClient.get<ProjectListResponse>('/api/v1/projects', { params });
    return res.data;
  },

  get: async (id: string): Promise<Project> => {
    const res = await apiClient.get<Project>(`/api/v1/projects/${id}`);
    return res.data;
  },

  create: async (payload: ProjectCreatePayload): Promise<Project> => {
    const res = await apiClient.post<Project>('/api/v1/projects', payload);
    return res.data;
  },

  update: async (id: string, payload: ProjectUpdatePayload): Promise<Project> => {
    const res = await apiClient.patch<Project>(`/api/v1/projects/${id}`, payload);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/projects/${id}`);
  },

  archive: async (id: string): Promise<Project> => {
    const res = await apiClient.patch<Project>(`/api/v1/projects/${id}/archive`);
    return res.data;
  },

  restore: async (id: string): Promise<Project> => {
    const res = await apiClient.patch<Project>(`/api/v1/projects/${id}/restore`);
    return res.data;
  },

  getStatistics: async (id: string): Promise<ProjectStatistics> => {
    const res = await apiClient.get<ProjectStatistics>(`/api/v1/projects/${id}/statistics`);
    return res.data;
  },

  listTasks: async (id: string, params?: ProjectTaskFilterParams): Promise<TaskListResponse> => {
    const res = await apiClient.get<TaskListResponse>(`/api/v1/projects/${id}/tasks`, { params });
    return res.data;
  },

  assignTask: async (projectId: string, taskId: string): Promise<Task> => {
    const res = await apiClient.put<Task>(`/api/v1/projects/${projectId}/tasks/${taskId}`);
    return res.data;
  },

  removeTask: async (projectId: string, taskId: string): Promise<Task> => {
    const res = await apiClient.delete<Task>(`/api/v1/projects/${projectId}/tasks/${taskId}`);
    return res.data;
  },
};

