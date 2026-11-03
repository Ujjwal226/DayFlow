import { apiClient } from './client';
import { Category, CategoryCreatePayload, CategoryUpdatePayload } from '../types/category';
import { TaskListResponse } from '../types/task';
import { MessageResponse } from '../types/auth';

export const categoriesApi = {
  listCategories: async (): Promise<Category[]> => {
    const response = await apiClient.get<Category[]>('/api/v1/categories');
    return response.data;
  },

  getCategory: async (categoryId: string): Promise<Category> => {
    const response = await apiClient.get<Category>(`/api/v1/categories/${categoryId}`);
    return response.data;
  },

  createCategory: async (payload: CategoryCreatePayload): Promise<Category> => {
    const response = await apiClient.post<Category>('/api/v1/categories', payload);
    return response.data;
  },

  updateCategory: async (categoryId: string, payload: CategoryUpdatePayload): Promise<Category> => {
    const response = await apiClient.patch<Category>(`/api/v1/categories/${categoryId}`, payload);
    return response.data;
  },

  deleteCategory: async (categoryId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/categories/${categoryId}`);
    return response.data;
  },

  getCategoryTasks: async (categoryId: string, page = 1, pageSize = 20): Promise<TaskListResponse> => {
    const response = await apiClient.get<TaskListResponse>(`/api/v1/categories/${categoryId}/tasks`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};

