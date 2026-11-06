import { describe, it, expect, vi, beforeEach, MockedFunction } from 'vitest';
import { dashboardApi } from '../api/dashboard';
import { apiClient } from '../api/client';
import { DashboardWidgetConfig } from '../types/dashboard';

vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Dashboard API Service', () => {
  const mockGet = apiClient.get as unknown as MockedFunction<typeof apiClient.get>;
  const mockPut = apiClient.put as unknown as MockedFunction<typeof apiClient.put>;
  const mockPost = apiClient.post as unknown as MockedFunction<typeof apiClient.post>;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockWidgets: DashboardWidgetConfig[] = [
    { widget_id: 'welcome', is_visible: true, order: 0, size: 'full' },
    { widget_id: 'productivity_overview', is_visible: true, order: 1, size: 'full' },
    { widget_id: 'today_tasks', is_visible: true, order: 2, size: 'medium' },
    { widget_id: 'upcoming_tasks', is_visible: true, order: 3, size: 'medium' },
    { widget_id: 'overdue_tasks', is_visible: true, order: 4, size: 'medium' },
    { widget_id: 'recent_activity', is_visible: true, order: 5, size: 'medium' },
    { widget_id: 'projects_overview', is_visible: true, order: 6, size: 'medium' },
    { widget_id: 'productivity_trends', is_visible: true, order: 7, size: 'medium' },
    { widget_id: 'recurring_insights', is_visible: true, order: 8, size: 'medium' },
    { widget_id: 'quick_actions', is_visible: true, order: 9, size: 'full' },
  ];

  it('calls GET /api/v1/dashboard/layout and returns layout response', async () => {
    const mockResponse = {
      id: null,
      user_id: 'user-123',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    };
    mockGet.mockResolvedValueOnce({ data: mockResponse });

    const result = await dashboardApi.getLayout();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/dashboard/layout');
    expect(result).toEqual(mockResponse);
  });

  it('calls PUT /api/v1/dashboard/layout with payload and returns updated layout', async () => {
    const mockResponse = {
      id: 'layout-uuid-1',
      user_id: 'user-123',
      widgets: mockWidgets,
      is_customized: true,
      created_at: '2026-11-07T00:00:00Z',
      updated_at: '2026-11-07T00:00:00Z',
    };
    mockPut.mockResolvedValueOnce({ data: mockResponse });

    const result = await dashboardApi.updateLayout(mockWidgets);
    expect(apiClient.put).toHaveBeenCalledWith('/api/v1/dashboard/layout', {
      widgets: mockWidgets,
    });
    expect(result).toEqual(mockResponse);
  });

  it('calls POST /api/v1/dashboard/layout/reset and returns default layout', async () => {
    const mockResponse = {
      id: null,
      user_id: 'user-123',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    };
    mockPost.mockResolvedValueOnce({ data: mockResponse });

    const result = await dashboardApi.resetLayout();
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/dashboard/layout/reset');
    expect(result).toEqual(mockResponse);
  });

  it('propagates API client errors correctly', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'));
    await expect(dashboardApi.getLayout()).rejects.toThrow('Network error');
  });
});
