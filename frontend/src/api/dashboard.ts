import { apiClient } from './client';
import {
  DashboardLayoutResponse,
  DashboardLayoutUpdateRequest,
  DashboardWidgetConfig,
} from '../types/dashboard';

export const dashboardApi = {
  getLayout: async (): Promise<DashboardLayoutResponse> => {
    const response = await apiClient.get<DashboardLayoutResponse>('/api/v1/dashboard/layout');
    return response.data;
  },

  updateLayout: async (widgets: DashboardWidgetConfig[]): Promise<DashboardLayoutResponse> => {
    const payload: DashboardLayoutUpdateRequest = { widgets };
    const response = await apiClient.put<DashboardLayoutResponse>(
      '/api/v1/dashboard/layout',
      payload
    );
    return response.data;
  },

  resetLayout: async (): Promise<DashboardLayoutResponse> => {
    const response = await apiClient.post<DashboardLayoutResponse>(
      '/api/v1/dashboard/layout/reset'
    );
    return response.data;
  },
};

