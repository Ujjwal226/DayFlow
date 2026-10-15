/**
 * DayFlow API client – centralised fetch wrapper.
 *
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 * All requests go to the FastAPI backend; no data is stored locally.
 */
import type {
  AnalyticsResponse,
  HealthResponse,
  MessageResponse,
  Task,
  TaskCreate,
  TaskEvent,
  TaskFilters,
  TaskListResponse,
  TaskReschedule,
  TaskUpdate,
  TokenResponse,
  User,
  UserLogin,
  UserRegister,
} from '../types/api';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
export const TOKEN_STORAGE_KEY = 'dayflow_token';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

// ─── Low-level fetch helper ───────────────────────────────────────────────────

class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(
    status: number,
    message: string,
    detail?: unknown,
  ) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const token = getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...init,
    headers,
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const message =
      typeof detail === 'object' && detail !== null && 'detail' in detail
        ? String((detail as { detail: unknown }).detail)
        : `HTTP ${res.status}`;

    // If 401 Unauthorized on protected routes, trigger event for auth state
    if (res.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
      clearAuthToken();
      window.dispatchEvent(new Event('dayflow:auth_unauthorized'));
    }

    throw new ApiError(res.status, message, detail);
  }

  // 204 No Content or empty body
  const text = await res.text();
  return text ? (JSON.parse(text) as T) : (undefined as unknown as T);
}

// ─── Authentication ───────────────────────────────────────────────────────────

export const authApi = {
  register: (payload: UserRegister): Promise<TokenResponse> =>
    request<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: UserLogin): Promise<TokenResponse> =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  me: (): Promise<User> => request<User>('/auth/me'),

  logout: (): Promise<MessageResponse> =>
    request<MessageResponse>('/auth/logout', { method: 'POST' }),
};

// ─── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => request<HealthResponse>('/health'),
};

// ─── Tasks ────────────────────────────────────────────────────────────────────

export const tasksApi = {
  list: (filters: TaskFilters = {}): Promise<TaskListResponse> => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.category) params.set('category', filters.category);
    if (filters.priority) params.set('priority', filters.priority);
    if (filters.skip !== undefined) params.set('skip', String(filters.skip));
    if (filters.limit !== undefined) params.set('limit', String(filters.limit));
    const qs = params.toString();
    return request<TaskListResponse>(`/tasks${qs ? `?${qs}` : ''}`);
  },

  get: (id: number): Promise<Task> => request<Task>(`/tasks/${id}`),

  create: (payload: TaskCreate): Promise<Task> =>
    request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  update: (id: number, payload: TaskUpdate): Promise<Task> =>
    request<Task>(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  complete: (id: number): Promise<Task> =>
    request<Task>(`/tasks/${id}/complete`, { method: 'PATCH' }),

  reopen: (id: number): Promise<Task> =>
    request<Task>(`/tasks/${id}/reopen`, { method: 'PATCH' }),

  reschedule: (id: number, payload: TaskReschedule): Promise<Task> =>
    request<Task>(`/tasks/${id}/reschedule`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getHistoryByDate: (targetDate: string, includeDeleted = true): Promise<Task[]> => {
    const qs = includeDeleted ? '?include_deleted=true' : '?include_deleted=false';
    return request<Task[]>(`/tasks/history/date/${targetDate}${qs}`);
  },

  getTaskHistory: (id: number): Promise<TaskEvent[]> =>
    request<TaskEvent[]>(`/tasks/${id}/history`),

  delete: (id: number): Promise<MessageResponse> =>
    request<MessageResponse>(`/tasks/${id}`, { method: 'DELETE' }),
};

// ─── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  /** Fetch comprehensive analytics. heatmap_days controls heatmap window (default 84 = 12 weeks). */
  get: (days = 84): Promise<AnalyticsResponse> =>
    request<AnalyticsResponse>(`/analytics?days=${days}`),
};

export { ApiError };
