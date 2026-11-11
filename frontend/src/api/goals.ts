import { apiClient } from './client';
import {
  Goal,
  GoalActivity,
  GoalAnalyticsOverview,
  GoalCreatePayload,
  GoalFilterParams,
  GoalListResponse,
  GoalUpdatePayload,
  Milestone,
  MilestoneCreatePayload,
  MilestoneReorderItem,
  MilestoneUpdatePayload,
  PlanningObjective,
  PlanningObjectiveCreatePayload,
  PlanningObjectiveUpdatePayload,
  PlanningPeriodSummary,
} from '../types/goal';

export const goalsApi = {
  createGoal: async (payload: GoalCreatePayload): Promise<Goal> => {
    const res = await apiClient.post<Goal>('/api/v1/goals', payload);
    return res.data;
  },

  listGoals: async (params?: GoalFilterParams): Promise<GoalListResponse> => {
    const res = await apiClient.get<GoalListResponse>('/api/v1/goals', { params });
    return res.data;
  },

  getGoal: async (goalId: string): Promise<Goal> => {
    const res = await apiClient.get<Goal>(`/api/v1/goals/${goalId}`);
    return res.data;
  },

  updateGoal: async (goalId: string, payload: GoalUpdatePayload): Promise<Goal> => {
    const res = await apiClient.patch<Goal>(`/api/v1/goals/${goalId}`, payload);
    return res.data;
  },

  deleteGoal: async (goalId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/goals/${goalId}`);
  },

  completeGoal: async (goalId: string): Promise<Goal> => {
    const res = await apiClient.post<Goal>(`/api/v1/goals/${goalId}/complete`);
    return res.data;
  },

  reopenGoal: async (goalId: string): Promise<Goal> => {
    const res = await apiClient.post<Goal>(`/api/v1/goals/${goalId}/reopen`);
    return res.data;
  },

  getGoalActivities: async (goalId: string): Promise<GoalActivity[]> => {
    const res = await apiClient.get<GoalActivity[]>(`/api/v1/goals/${goalId}/activities`);
    return res.data;
  },

  getAnalytics: async (): Promise<GoalAnalyticsOverview> => {
    const res = await apiClient.get<GoalAnalyticsOverview>('/api/v1/goals/analytics');
    return res.data;
  },

  // Milestones
  createMilestone: async (goalId: string, payload: MilestoneCreatePayload): Promise<Milestone> => {
    const res = await apiClient.post<Milestone>(`/api/v1/goals/${goalId}/milestones`, payload);
    return res.data;
  },

  updateMilestone: async (milestoneId: string, payload: MilestoneUpdatePayload): Promise<Milestone> => {
    const res = await apiClient.patch<Milestone>(`/api/v1/goals/milestones/${milestoneId}`, payload);
    return res.data;
  },

  deleteMilestone: async (milestoneId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/goals/milestones/${milestoneId}`);
  },

  reorderMilestones: async (goalId: string, items: MilestoneReorderItem[]): Promise<Milestone[]> => {
    const res = await apiClient.post<Milestone[]>(`/api/v1/goals/${goalId}/milestones/reorder`, items);
    return res.data;
  },

  // Task Relationships
  linkTask: async (goalId: string, taskId: string): Promise<Goal> => {
    const res = await apiClient.post<Goal>(`/api/v1/goals/${goalId}/tasks`, { task_id: taskId });
    return res.data;
  },

  unlinkTask: async (goalId: string, taskId: string): Promise<Goal> => {
    const res = await apiClient.delete<Goal>(`/api/v1/goals/${goalId}/tasks/${taskId}`);
    return res.data;
  },

  // Planning Objectives
  createPlanningObjective: async (payload: PlanningObjectiveCreatePayload): Promise<PlanningObjective> => {
    const res = await apiClient.post<PlanningObjective>('/api/v1/goals/planning/objectives', payload);
    return res.data;
  },

  getPlanningSummary: async (periodType: string = 'DAILY', periodDate?: string): Promise<PlanningPeriodSummary> => {
    const res = await apiClient.get<PlanningPeriodSummary>('/api/v1/goals/planning/summary', {
      params: { period_type: periodType, period_date: periodDate },
    });
    return res.data;
  },

  updatePlanningObjective: async (
    objectiveId: string,
    payload: PlanningObjectiveUpdatePayload
  ): Promise<PlanningObjective> => {
    const res = await apiClient.patch<PlanningObjective>(`/api/v1/goals/planning/objectives/${objectiveId}`, payload);
    return res.data;
  },

  deletePlanningObjective: async (objectiveId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/goals/planning/objectives/${objectiveId}`);
  },
};
