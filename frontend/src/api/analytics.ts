import { apiClient } from './client';
import {
  ProductivityOverviewResponse,
  ProductivityTrendsResponse,
  ConsistencyAnalyticsResponse,
  ProjectAnalyticsResponse,
  CategoryAnalyticsResponse,
  WorkloadAnalyticsResponse,
  RecurringAnalyticsResponse,
  AnalyticsTrendsParams,
  AnalyticsOverviewParams,
} from '../types/analytics';

export const analyticsApi = {
  getOverview: async (
    params: AnalyticsOverviewParams = {}
  ): Promise<ProductivityOverviewResponse> => {
    const cleanParams: Record<string, string | number> = {};
    if (params.start_date) cleanParams.start_date = params.start_date;
    if (params.end_date) cleanParams.end_date = params.end_date;
    if (params.days !== undefined) cleanParams.days = params.days;

    const response = await apiClient.get<ProductivityOverviewResponse>(
      '/api/v1/analytics/overview',
      { params: cleanParams }
    );
    return response.data;
  },

  getTrends: async (
    params: AnalyticsTrendsParams = {}
  ): Promise<ProductivityTrendsResponse> => {
    const cleanParams: Record<string, string | number> = {};
    if (params.interval) cleanParams.interval = params.interval;
    if (params.days !== undefined) cleanParams.days = params.days;
    if (params.start_date) cleanParams.start_date = params.start_date;
    if (params.end_date) cleanParams.end_date = params.end_date;
    if (params.timezone) cleanParams.timezone = params.timezone;

    const response = await apiClient.get<ProductivityTrendsResponse>(
      '/api/v1/analytics/trends',
      { params: cleanParams }
    );
    return response.data;
  },

  getConsistency: async (timezone?: string): Promise<ConsistencyAnalyticsResponse> => {
    const response = await apiClient.get<ConsistencyAnalyticsResponse>(
      '/api/v1/analytics/consistency',
      { params: timezone ? { timezone } : {} }
    );
    return response.data;
  },

  getProjects: async (): Promise<ProjectAnalyticsResponse> => {
    const response = await apiClient.get<ProjectAnalyticsResponse>(
      '/api/v1/analytics/projects'
    );
    return response.data;
  },

  getCategories: async (): Promise<CategoryAnalyticsResponse> => {
    const response = await apiClient.get<CategoryAnalyticsResponse>(
      '/api/v1/analytics/categories'
    );
    return response.data;
  },

  getWorkload: async (timezone?: string): Promise<WorkloadAnalyticsResponse> => {
    const response = await apiClient.get<WorkloadAnalyticsResponse>(
      '/api/v1/analytics/workload',
      { params: timezone ? { timezone } : {} }
    );
    return response.data;
  },

  getRecurring: async (timezone?: string): Promise<RecurringAnalyticsResponse> => {
    const response = await apiClient.get<RecurringAnalyticsResponse>(
      '/api/v1/analytics/recurring',
      { params: timezone ? { timezone } : {} }
    );
    return response.data;
  },
};

