import { apiClient } from './client';
import {
  FocusSession,
  FocusSessionActiveResponse,
  FocusSessionStartPayload,
  FocusPreference,
  FocusPreferenceUpdatePayload,
  FocusAnalyticsOverview,
} from '../types/focus';

export const focusApi = {
  getActiveSession: async (): Promise<FocusSessionActiveResponse | null> => {
    const res = await apiClient.get<FocusSessionActiveResponse | null>('/api/v1/focus/active');
    return res.data;
  },

  startSession: async (payload: FocusSessionStartPayload = {}): Promise<FocusSessionActiveResponse> => {
    const res = await apiClient.post<FocusSessionActiveResponse>('/api/v1/focus/start', payload);
    return res.data;
  },

  pauseSession: async (sessionId: string): Promise<FocusSessionActiveResponse> => {
    const res = await apiClient.post<FocusSessionActiveResponse>(`/api/v1/focus/sessions/${sessionId}/pause`);
    return res.data;
  },

  resumeSession: async (sessionId: string): Promise<FocusSessionActiveResponse> => {
    const res = await apiClient.post<FocusSessionActiveResponse>(`/api/v1/focus/sessions/${sessionId}/resume`);
    return res.data;
  },

  completeSession: async (sessionId: string): Promise<FocusSession> => {
    const res = await apiClient.post<FocusSession>(`/api/v1/focus/sessions/${sessionId}/complete`);
    return res.data;
  },

  abandonSession: async (sessionId: string): Promise<FocusSession> => {
    const res = await apiClient.post<FocusSession>(`/api/v1/focus/sessions/${sessionId}/abandon`);
    return res.data;
  },

  skipSession: async (sessionId: string): Promise<FocusSessionActiveResponse> => {
    const res = await apiClient.post<FocusSessionActiveResponse>(`/api/v1/focus/sessions/${sessionId}/skip`);
    return res.data;
  },

  getSession: async (sessionId: string): Promise<FocusSessionActiveResponse> => {
    const res = await apiClient.get<FocusSessionActiveResponse>(`/api/v1/focus/sessions/${sessionId}`);
    return res.data;
  },

  getSessionHistory: async (limit: number = 20): Promise<FocusSession[]> => {
    const res = await apiClient.get<FocusSession[]>('/api/v1/focus/history', { params: { limit } });
    return res.data;
  },

  getPreferences: async (): Promise<FocusPreference> => {
    const res = await apiClient.get<FocusPreference>('/api/v1/focus/preferences');
    return res.data;
  },

  updatePreferences: async (payload: FocusPreferenceUpdatePayload): Promise<FocusPreference> => {
    const res = await apiClient.patch<FocusPreference>('/api/v1/focus/preferences', payload);
    return res.data;
  },

  getAnalytics: async (): Promise<FocusAnalyticsOverview> => {
    const res = await apiClient.get<FocusAnalyticsOverview>('/api/v1/focus/analytics');
    return res.data;
  },
};
