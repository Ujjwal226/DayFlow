import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { TokenResponse } from '../types/auth';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// In-memory token management
let inMemoryAccessToken: string | null = null;
let onTokenExpiredCallback: (() => void) | null = null;

export const setAccessToken = (token: string | null): void => {
  inMemoryAccessToken = token;
};

export const getAccessToken = (): string | null => {
  return inMemoryAccessToken;
};

export const setOnTokenExpired = (callback: () => void): void => {
  onTokenExpiredCallback = callback;
};

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  withCredentials: true, // Always send HttpOnly refresh cookies
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Attach in-memory access token to protected requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (inMemoryAccessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Single-flight refresh token coordination
let refreshPromise: Promise<string | null> | null = null;

export const executeTokenRefresh = async (): Promise<string | null> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      // Call refresh endpoint with credentials (HttpOnly cookie)
      const response = await axios.post<TokenResponse>(
        `${apiBaseUrl}/api/v1/auth/refresh`,
        {},
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
        }
      );
      const newToken = response.data.access_token;
      setAccessToken(newToken);
      return newToken;
    } catch {
      setAccessToken(null);
      if (onTokenExpiredCallback) {
        onTokenExpiredCallback();
      }
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

// Response interceptor with auto-refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Do not attempt refresh on auth endpoints (login, register, refresh, logout, logout-all)
    const isAuthEndpoint =
      originalRequest?.url?.includes('/api/v1/auth/login') ||
      originalRequest?.url?.includes('/api/v1/auth/register') ||
      originalRequest?.url?.includes('/api/v1/auth/refresh') ||
      originalRequest?.url?.includes('/api/v1/auth/logout') ||
      originalRequest?.url?.includes('/api/v1/auth/logout-all');

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const newToken = await executeTokenRefresh();

      if (newToken && originalRequest) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      }
    }

    // Parse and extract clean backend error message
    let errorMessage = 'An unexpected error occurred.';
    if (error.response?.data && typeof error.response.data === 'object') {
      const data = error.response.data as Record<string, unknown>;
      errorMessage = (data.detail as string) || (data.message as string) || JSON.stringify(data);
    } else if (error.message) {
      errorMessage = error.message;
    }

    return Promise.reject(new Error(errorMessage));
  }
);
