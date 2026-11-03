import { apiClient } from './client';
import { Tag, TagCreatePayload, TagUpdatePayload } from '../types/tag';
import { MessageResponse } from '../types/auth';

export const tagsApi = {
  listTags: async (): Promise<Tag[]> => {
    const response = await apiClient.get<Tag[]>('/api/v1/tags');
    return response.data;
  },

  getTag: async (tagId: string): Promise<Tag> => {
    const response = await apiClient.get<Tag>(`/api/v1/tags/${tagId}`);
    return response.data;
  },

  createTag: async (payload: TagCreatePayload): Promise<Tag> => {
    const response = await apiClient.post<Tag>('/api/v1/tags', payload);
    return response.data;
  },

  updateTag: async (tagId: string, payload: TagUpdatePayload): Promise<Tag> => {
    const response = await apiClient.patch<Tag>(`/api/v1/tags/${tagId}`, payload);
    return response.data;
  },

  deleteTag: async (tagId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/tags/${tagId}`);
    return response.data;
  },
};

