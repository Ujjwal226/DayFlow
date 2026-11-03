import { apiClient } from './client';
import { Subtask, SubtaskCreatePayload, SubtaskUpdatePayload } from '../types/subtask';
import { MessageResponse } from '../types/auth';

export const subtasksApi = {
  createSubtask: async (parentTaskId: string, payload: SubtaskCreatePayload): Promise<Subtask> => {
    const response = await apiClient.post<Subtask>(`/api/v1/tasks/${parentTaskId}/subtasks`, payload);
    return response.data;
  },

  listSubtasks: async (parentTaskId: string): Promise<Subtask[]> => {
    const response = await apiClient.get<Subtask[]>(`/api/v1/tasks/${parentTaskId}/subtasks`);
    return response.data;
  },

  getSubtask: async (subtaskId: string): Promise<Subtask> => {
    const response = await apiClient.get<Subtask>(`/api/v1/subtasks/${subtaskId}`);
    return response.data;
  },

  updateSubtask: async (subtaskId: string, payload: SubtaskUpdatePayload): Promise<Subtask> => {
    const response = await apiClient.patch<Subtask>(`/api/v1/subtasks/${subtaskId}`, payload);
    return response.data;
  },

  deleteSubtask: async (subtaskId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/subtasks/${subtaskId}`);
    return response.data;
  },
};

