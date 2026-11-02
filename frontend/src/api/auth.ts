import { apiClient, executeTokenRefresh, setAccessToken } from './client';
import {
  MessageResponse,
  TokenResponse,
  User,
  UserLoginRequest,
  UserRegisterRequest,
} from '../types/auth';

export const authApi = {
  register: async (payload: UserRegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/api/v1/auth/register', payload);
    return response.data;
  },

  login: async (credentials: UserLoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', credentials);
    setAccessToken(response.data.access_token);
    return response.data;
  },

  refresh: async (): Promise<string | null> => {
    return executeTokenRefresh();
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },

  logout: async (): Promise<MessageResponse> => {
    try {
      const response = await apiClient.post<MessageResponse>('/api/v1/auth/logout');
      return response.data;
    } finally {
      setAccessToken(null);
    }
  },

  logoutAll: async (): Promise<MessageResponse> => {
    try {
      const response = await apiClient.post<MessageResponse>('/api/v1/auth/logout-all');
      return response.data;
    } finally {
      setAccessToken(null);
    }
  },
};

