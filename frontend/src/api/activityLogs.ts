import { apiClient } from './client';
import {
  ActivityLogListResponse,
  ActivityLogQueryParams,
} from '../types/activityLog';

export const activityLogsApi = {
  getGlobalActivities: async (
    params: ActivityLogQueryParams = {}
  ): Promise<ActivityLogListResponse> => {
    const cleanParams: Record<string, string | number> = {};
    if (params.action) cleanParams.action = params.action;
    if (params.entity_type) cleanParams.entity_type = params.entity_type;
    if (params.task_id) cleanParams.task_id = params.task_id;
    if (params.recurring_task_id) cleanParams.recurring_task_id = params.recurring_task_id;
    if (params.start_date) cleanParams.start_date = params.start_date;
    if (params.end_date) cleanParams.end_date = params.end_date;
    if (params.page !== undefined) cleanParams.page = params.page;
    if (params.page_size !== undefined) cleanParams.page_size = params.page_size;

    const response = await apiClient.get<ActivityLogListResponse>('/activity-logs', {
      params: cleanParams,
    });
    return response.data;
  },

  getTaskActivityTimeline: async (
    taskId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ActivityLogListResponse> => {
    const response = await apiClient.get<ActivityLogListResponse>(
      `/tasks/${taskId}/activity`,
      {
        params: {
          page,
          page_size: pageSize,
        },
      }
    );
    return response.data;
  },
};
