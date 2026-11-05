import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ActivityPage } from '../pages/ActivityPage';
import { ActivityItem } from '../components/activity/ActivityItem';
import { ActivityFilters } from '../components/activity/ActivityFilters';
import { ActivityTimeline } from '../components/activity/ActivityTimeline';
import { activityLogsApi } from '../api/activityLogs';
import { ActivityLog } from '../types/activityLog';

vi.mock('../api/activityLogs');
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@example.com', display_name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

const mockLogs: ActivityLog[] = [
  {
    id: 'log-1',
    user_id: 'user-1',
    actor_id: 'user-1',
    task_id: 'task-100',
    recurring_task_id: null,
    entity_type: 'TASK',
    entity_id: 'task-100',
    action: 'TASK_CREATED',
    changes: null,
    metadata: { title: 'Implement Authentication Engine' },
    created_at: '2026-11-05T10:00:00Z',
  },
  {
    id: 'log-2',
    user_id: 'user-1',
    actor_id: 'user-1',
    task_id: 'task-100',
    recurring_task_id: null,
    entity_type: 'TASK',
    entity_id: 'task-100',
    action: 'TASK_UPDATED',
    changes: {
      status: { old: 'TODO', new: 'COMPLETED' },
    },
    metadata: { title: 'Implement Authentication Engine' },
    created_at: '2026-11-05T11:30:00Z',
  },
  {
    id: 'log-3',
    user_id: 'user-1',
    actor_id: 'user-1',
    task_id: null,
    recurring_task_id: null,
    entity_type: 'PROJECT',
    entity_id: 'proj-200',
    action: 'PROJECT_CREATED',
    changes: null,
    metadata: { name: 'DayFlow Q4 Launch' },
    created_at: '2026-11-05T12:00:00Z',
  },
];

describe('Activity History & Activity Tracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ActivityItem Component', () => {
    it('renders task creation event and title', () => {
      render(<ActivityItem activity={mockLogs[0]} />);
      expect(screen.getByText('Task created')).toBeInTheDocument();
      expect(screen.getByText('TASK')).toBeInTheDocument();
      expect(screen.getByText('Implement Authentication Engine')).toBeInTheDocument();
    });

    it('renders status changes diff correctly', () => {
      render(<ActivityItem activity={mockLogs[1]} />);
      expect(screen.getByText('Task updated')).toBeInTheDocument();
      expect(screen.getByText('status:')).toBeInTheDocument();
      expect(screen.getByText('TODO')).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });

    it('renders project creation event', () => {
      render(<ActivityItem activity={mockLogs[2]} />);
      expect(screen.getByText('Project created')).toBeInTheDocument();
      expect(screen.getByText('PROJECT')).toBeInTheDocument();
      expect(screen.getByText('DayFlow Q4 Launch')).toBeInTheDocument();
    });
  });

  describe('ActivityFilters Component', () => {
    it('triggers filter updates on change', () => {
      const setAction = vi.fn();
      const setEntity = vi.fn();
      const setStart = vi.fn();
      const setEnd = vi.fn();
      const onReset = vi.fn();

      render(
        <ActivityFilters
          actionFilter=""
          setActionFilter={setAction}
          entityFilter=""
          setEntityFilter={setEntity}
          startDate=""
          setStartDate={setStart}
          endDate=""
          setEndDate={setEnd}
          onReset={onReset}
        />
      );

      const selects = screen.getAllByRole('combobox');
      // Entity select
      fireEvent.change(selects[0], { target: { value: 'PROJECT' } });
      expect(setEntity).toHaveBeenCalledWith('PROJECT');

      // Action select
      fireEvent.change(selects[1], { target: { value: 'TASK_COMPLETED' } });
      expect(setAction).toHaveBeenCalledWith('TASK_COMPLETED');

      // Reset button
      const resetBtn = screen.getByRole('button', { name: /reset/i });
      fireEvent.click(resetBtn);
      expect(onReset).toHaveBeenCalled();
    });
  });

  describe('ActivityPage Feed & Pagination', () => {
    it('renders global activity feed with items', async () => {
      vi.mocked(activityLogsApi.getGlobalActivities).mockResolvedValueOnce({
        items: mockLogs,
        total: 3,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      render(
        <BrowserRouter>
          <ActivityPage />
        </BrowserRouter>
      );

      expect(screen.getByText(/loading activity feed/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Activity Feed')).toBeInTheDocument();
        expect(screen.getAllByText('Implement Authentication Engine')).toHaveLength(2);
        expect(screen.getByText('DayFlow Q4 Launch')).toBeInTheDocument();
      });
    });

    it('renders empty feed state when no activity recorded', async () => {
      vi.mocked(activityLogsApi.getGlobalActivities).mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        total_pages: 0,
      });

      render(
        <BrowserRouter>
          <ActivityPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No activity recorded yet')).toBeInTheDocument();
      });
    });
  });

  describe('ActivityTimeline Component for Task Details', () => {
    it('fetches and renders task-specific activity timeline', async () => {
      vi.mocked(activityLogsApi.getTaskActivityTimeline).mockResolvedValueOnce({
        items: [mockLogs[0], mockLogs[1]],
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      });

      render(
        <MemoryRouter>
          <ActivityTimeline taskId="task-100" />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Task created')).toBeInTheDocument();
        expect(screen.getByText('Task updated')).toBeInTheDocument();
      });
      expect(activityLogsApi.getTaskActivityTimeline).toHaveBeenCalledWith('task-100', 1, 10);
    });
  });
});
