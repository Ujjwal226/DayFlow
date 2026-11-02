import { apiClient } from './client';
import { RootResponse, LivenessResponse, ReadinessResponse } from '../types/api';

export const healthApi = {
  getRoot: async (): Promise<RootResponse> => {
    const response = await apiClient.get<RootResponse>('/');
    return response.data;
  },

  getLiveness: async (): Promise<LivenessResponse> => {
    const response = await apiClient.get<LivenessResponse>('/api/v1/health/live');
    return response.data;
  },

  getReadiness: async (): Promise<ReadinessResponse> => {
    const response = await apiClient.get<ReadinessResponse>('/api/v1/health/ready');
    return response.data;
  },
};

