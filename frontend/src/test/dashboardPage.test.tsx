import { describe, it, expect, vi, beforeEach, MockedFunction } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/DashboardPage';
import { dashboardApi } from '../api/dashboard';
import { DashboardWidgetConfig } from '../types/dashboard';

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-uuid-1',
      email: 'test@example.com',
      display_name: 'Test Member',
      is_verified: true,
      created_at: '2026-11-01T00:00:00Z',
    },
    logout: vi.fn(),
    logoutAll: vi.fn(),
    resendVerification: vi.fn(),
    isLoading: false,
  }),
}));

// Mock dashboardApi
vi.mock('../api/dashboard', () => ({
  dashboardApi: {
    getLayout: vi.fn(),
    updateLayout: vi.fn(),
    resetLayout: vi.fn(),
  },
}));

// Mock widgets to isolate page behavior
vi.mock('../components/dashboard/widgets/WelcomeWidget', () => ({
  WelcomeWidget: () => <div data-testid="widget-welcome">Welcome Widget Mock</div>,
}));

vi.mock('../components/dashboard/widgets/TodayTasksWidget', () => ({
  TodayTasksWidget: () => <div data-testid="widget-today_tasks">Today Tasks Mock</div>,
}));

vi.mock('../components/dashboard/widgets/QuickActionsWidget', () => ({
  QuickActionsWidget: () => <div data-testid="widget-quick_actions">Quick Actions Mock</div>,
}));

describe('DashboardPage Component', () => {
  const mockGetLayout = dashboardApi.getLayout as unknown as MockedFunction<typeof dashboardApi.getLayout>;
  const mockUpdateLayout = dashboardApi.updateLayout as unknown as MockedFunction<typeof dashboardApi.updateLayout>;
  const mockResetLayout = dashboardApi.resetLayout as unknown as MockedFunction<typeof dashboardApi.resetLayout>;

  const mockWidgets: DashboardWidgetConfig[] = [
    { widget_id: 'welcome', is_visible: true, order: 0, size: 'full' },
    { widget_id: 'today_tasks', is_visible: true, order: 1, size: 'medium' },
    { widget_id: 'quick_actions', is_visible: false, order: 2, size: 'full' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and renders layout on mount', async () => {
    mockGetLayout.mockResolvedValueOnce({
      id: null,
      user_id: 'user-uuid-1',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Loading your dashboard layout...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('widget-welcome')).toBeInTheDocument();
      expect(screen.getByTestId('widget-today_tasks')).toBeInTheDocument();
      expect(screen.queryByTestId('widget-quick_actions')).not.toBeInTheDocument();
    });
  });

  it('handles layout loading error and allows retry', async () => {
    mockGetLayout.mockRejectedValueOnce(new Error('Network failure'));

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Layout Unavailable')).toBeInTheDocument();
    });

    // Retry successfully
    mockGetLayout.mockResolvedValueOnce({
      id: null,
      user_id: 'user-uuid-1',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    });

    const retryBtn = screen.getByRole('button', { name: /Retry Loading/i });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByTestId('widget-welcome')).toBeInTheDocument();
    });
  });

  it('opens customizer, saves changes, and updates displayed widgets', async () => {
    mockGetLayout.mockResolvedValueOnce({
      id: null,
      user_id: 'user-uuid-1',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('widget-welcome')).toBeInTheDocument();
    });

    // Open customizer
    const customizeBtn = screen.getByRole('button', { name: /Customize Dashboard/i });
    fireEvent.click(customizeBtn);

    expect(screen.getByText('Reorder, resize, and choose which widgets appear')).toBeInTheDocument();

    // Toggle quick_actions visible
    const quickActionsToggle = screen.getByRole('button', { name: /Show Quick Actions/i });
    fireEvent.click(quickActionsToggle);

    // Mock updateLayout response
    const updatedWidgets: DashboardWidgetConfig[] = [
      ...mockWidgets.slice(0, 2),
      { widget_id: 'quick_actions', is_visible: true, order: 2, size: 'full' },
    ];
    mockUpdateLayout.mockResolvedValueOnce({
      id: 'layout-uuid-saved',
      user_id: 'user-uuid-1',
      widgets: updatedWidgets,
      is_customized: true,
      created_at: '2026-11-07T00:00:00Z',
      updated_at: '2026-11-07T00:00:00Z',
    });

    // Click Save Layout
    const saveBtn = screen.getByRole('button', { name: /Save Layout/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      // Customizer closes and quick actions is now visible
      expect(screen.queryByText('Reorder, resize, and choose which widgets appear')).not.toBeInTheDocument();
      expect(screen.getByTestId('widget-quick_actions')).toBeInTheDocument();
    });
  });

  it('resets layout to defaults', async () => {
    mockGetLayout.mockResolvedValueOnce({
      id: 'saved-id',
      user_id: 'user-uuid-1',
      widgets: mockWidgets,
      is_customized: true,
      created_at: '2026-11-07T00:00:00Z',
      updated_at: '2026-11-07T00:00:00Z',
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('widget-welcome')).toBeInTheDocument();
    });

    // Open customizer
    fireEvent.click(screen.getByRole('button', { name: /Customize Dashboard/i }));

    // Mock reset response
    mockResetLayout.mockResolvedValueOnce({
      id: null,
      user_id: 'user-uuid-1',
      widgets: mockWidgets,
      is_customized: false,
      created_at: null,
      updated_at: null,
    });

    const resetBtn = screen.getByRole('button', { name: /Restore Defaults/i });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.queryByText('Reorder, resize, and choose which widgets appear')).not.toBeInTheDocument();
    });
  });
});
