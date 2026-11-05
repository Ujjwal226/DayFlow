import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { analyticsApi } from '../api/analytics';
import {
  ProductivityOverviewResponse,
  ProductivityTrendsResponse,
  ConsistencyAnalyticsResponse,
  ProjectAnalyticsResponse,
  CategoryAnalyticsResponse,
  WorkloadAnalyticsResponse,
  RecurringAnalyticsResponse,
} from '../types/analytics';

vi.mock('../api/analytics');
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'u1', email: 'test@dayflow.com', display_name: 'Test Dayflow' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

const mockOverview: ProductivityOverviewResponse = {
  total_tasks: 25,
  completed_tasks: 15,
  pending_tasks: 8,
  overdue_tasks: 2,
  cancelled_tasks: 2,
  completion_rate: 65.22,
  period_start: '2026-10-06T00:00:00Z',
  period_end: '2026-11-05T00:00:00Z',
  tasks_created_in_period: 12,
  tasks_completed_in_period: 14,
  tasks_reopened_in_period: 2,
  net_completions_in_period: 12,
};

const mockTrends: ProductivityTrendsResponse = {
  interval: 'daily',
  timezone: 'Asia/Kolkata',
  period_start: '2026-10-06',
  period_end: '2026-11-05',
  buckets: [
    {
      bucket_label: '2026-11-01',
      start_date: '2026-11-01',
      end_date: '2026-11-01',
      created_count: 3,
      gross_completions: 4,
      reopened_count: 1,
      net_completions: 3,
      unique_tasks_completed: 4,
    },
    {
      bucket_label: '2026-11-02',
      start_date: '2026-11-02',
      end_date: '2026-11-02',
      created_count: 1,
      gross_completions: 1,
      reopened_count: 3,
      net_completions: -2, // Negative net completion test case
      unique_tasks_completed: 1,
    },
  ],
  comparison: {
    current_period_completions: 5,
    prior_period_completions: 2,
    completion_change_percentage: 150.0,
    current_period_created: 4,
    prior_period_created: 6,
    created_change_percentage: -33.33,
  },
  historical_completeness_note:
    'Full historical tracking from Stage 2E onwards with pre-Stage 2E fallback.',
};

const mockConsistency: ConsistencyAnalyticsResponse = {
  current_streak_days: 4,
  longest_streak_days: 12,
  most_productive_weekday: 'Wednesday',
  weekday_completion_distribution: {
    Monday: 2,
    Tuesday: 4,
    Wednesday: 8,
    Thursday: 3,
    Friday: 5,
    Saturday: 1,
    Sunday: 0,
  },
  timezone: 'Asia/Kolkata',
  total_productive_days: 28,
  heatmap_365_days: [
    { date: '2026-11-01', count: 4, level: 3 },
    { date: '2026-11-02', count: 1, level: 1 },
    { date: '2026-11-03', count: 0, level: 0 },
    { date: '2026-11-04', count: 6, level: 4 },
  ],
};

const mockProjects: ProjectAnalyticsResponse = {
  total_projects: 2,
  projects: [
    {
      project_id: 'p1',
      project_name: 'Core Engine Launch',
      project_color: '#3b82f6',
      project_status: 'ACTIVE',
      total_tasks: 10,
      completed_tasks: 7,
      pending_tasks: 3,
      overdue_tasks: 1,
      completion_percentage: 70.0,
    },
    {
      project_id: 'p2',
      project_name: 'Mobile App Beta',
      project_color: '#10b981',
      project_status: 'ACTIVE',
      total_tasks: 5,
      completed_tasks: 5,
      pending_tasks: 0,
      overdue_tasks: 0,
      completion_percentage: 100.0,
    },
  ],
};

const mockCategories: CategoryAnalyticsResponse = {
  total_categories: 2,
  categories: [
    {
      category_id: 'c1',
      category_name: 'Backend Dev',
      category_color: '#8b5cf6',
      category_icon: 'server',
      total_tasks: 8,
      completed_tasks: 6,
      pending_tasks: 2,
      completion_rate: 75.0,
    },
    {
      category_id: null,
      category_name: 'Uncategorized',
      category_color: null,
      category_icon: null,
      total_tasks: 4,
      completed_tasks: 2,
      pending_tasks: 2,
      completion_rate: 50.0,
    },
  ],
};

const mockWorkload: WorkloadAnalyticsResponse = {
  total_pending_tasks: 8,
  priority_distribution: {
    urgent: 1,
    high: 2,
    medium: 4,
    low: 1,
  },
  horizons: {
    overdue: 2,
    due_today: 1,
    due_tomorrow: 1,
    due_next_7_days: 2,
    due_later: 1,
    no_due_date: 1,
  },
  timezone: 'Asia/Kolkata',
};

const mockRecurring: RecurringAnalyticsResponse = {
  total_series: 3,
  active_series: 2,
  paused_or_stopped_series: 1,
  total_generated_occurrences: 15,
  completed_occurrences: 10,
  pending_due_occurrences: 2,
  future_occurrences: 5,
  skipped_occurrences: 1,
  eligible_due_occurrences: 13,
  adherence_rate: 76.92,
  frequency_breakdown: {
    daily: 1,
    weekly: 1,
    monthly: 1,
    yearly: 0,
    custom: 0,
  },
  schema_limitations_note: 'Occurrences bounded within horizon limits.',
};

describe('Productivity Analytics Frontend Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(analyticsApi.getOverview).mockResolvedValue(mockOverview);
    vi.mocked(analyticsApi.getTrends).mockResolvedValue(mockTrends);
    vi.mocked(analyticsApi.getConsistency).mockResolvedValue(mockConsistency);
    vi.mocked(analyticsApi.getProjects).mockResolvedValue(mockProjects);
    vi.mocked(analyticsApi.getCategories).mockResolvedValue(mockCategories);
    vi.mocked(analyticsApi.getWorkload).mockResolvedValue(mockWorkload);
    vi.mocked(analyticsApi.getRecurring).mockResolvedValue(mockRecurring);
  });

  it('renders all productivity analytics sections with backend metrics', async () => {
    render(
      <MemoryRouter>
        <AnalyticsPage />
      </MemoryRouter>
    );

    // Header & page title
    expect(
      screen.getByText('Productivity Analytics & Insights')
    ).toBeInTheDocument();

    // Verify Overview KPI values
    await waitFor(() => {
      expect(screen.getByText('Total Tasks')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument(); // total tasks
      expect(screen.getByText('65.22%')).toBeInTheDocument(); // completion rate
    });

    // Verify Trends chart presence and period comparison
    expect(screen.getByText('Productivity Trends')).toBeInTheDocument();
    expect(screen.getByText('+150%')).toBeInTheDocument();

    // Verify negative net completion indicator in legend
    expect(
      screen.getByText('Negative net values present (reopened > completed)')
    ).toBeInTheDocument();

    // Verify Consistency section & streaks
    expect(
      screen.getByText('Productivity Consistency & Streaks')
    ).toBeInTheDocument();
    expect(screen.getByText('4 days')).toBeInTheDocument(); // current streak
    expect(screen.getByText('12 days')).toBeInTheDocument(); // best streak
    expect(screen.getByText('Wednesday')).toBeInTheDocument(); // most productive

    // Verify Project performance
    expect(screen.getByText('Project Performance')).toBeInTheDocument();
    expect(screen.getByText('Core Engine Launch')).toBeInTheDocument();
    expect(screen.getByText('Mobile App Beta')).toBeInTheDocument();
    expect(screen.getByText('70%')).toBeInTheDocument();

    // Verify Category breakdown
    expect(screen.getByText('Category Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Backend Dev')).toBeInTheDocument();
    expect(screen.getByText('Uncategorized')).toBeInTheDocument();

    // Verify Workload distribution
    expect(screen.getByText('Workload & Deadlines')).toBeInTheDocument();
    expect(screen.getByText('Urgent')).toBeInTheDocument();
    expect(screen.getAllByText('Overdue').length).toBeGreaterThanOrEqual(1);

    // Verify Recurring insights
    expect(screen.getByText('Recurring Task Insights')).toBeInTheDocument();
    expect(screen.getByText('76.92%')).toBeInTheDocument(); // adherence rate
    expect(screen.getByText('Eligible Due')).toBeInTheDocument();
  });

  it('handles date range preset changes and passes parameters to API', async () => {
    render(
      <MemoryRouter>
        <AnalyticsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(analyticsApi.getOverview).toHaveBeenCalledWith({
        days: 30,
        start_date: undefined,
        end_date: undefined,
      });
    });

    // Switch to 7 Days preset
    const btn7d = screen.getByRole('button', { name: '7 Days' });
    fireEvent.click(btn7d);

    await waitFor(() => {
      expect(analyticsApi.getOverview).toHaveBeenCalledWith({
        days: 7,
        start_date: undefined,
        end_date: undefined,
      });
      expect(analyticsApi.getTrends).toHaveBeenCalledWith(
        expect.objectContaining({
          days: 7,
        })
      );
    });

    // Switch aggregation interval to weekly
    const btnWeekly = screen.getByRole('button', { name: 'Weekly' });
    fireEvent.click(btnWeekly);

    await waitFor(() => {
      expect(analyticsApi.getTrends).toHaveBeenCalledWith(
        expect.objectContaining({
          interval: 'weekly',
        })
      );
    });

    // Change Timezone
    const tzSelect = screen.getByLabelText('Select Timezone');
    fireEvent.change(tzSelect, { target: { value: 'America/New_York' } });

    await waitFor(() => {
      expect(analyticsApi.getTrends).toHaveBeenCalledWith(
        expect.objectContaining({
          timezone: 'America/New_York',
        })
      );
      expect(analyticsApi.getConsistency).toHaveBeenCalledWith('America/New_York');
      expect(analyticsApi.getWorkload).toHaveBeenCalledWith('America/New_York');
      expect(analyticsApi.getRecurring).toHaveBeenCalledWith('America/New_York');
    });
  });

  it('renders custom date range inputs and validates range', async () => {
    render(
      <MemoryRouter>
        <AnalyticsPage />
      </MemoryRouter>
    );

    const btnCustom = screen.getByRole('button', { name: 'Custom' });
    fireEvent.click(btnCustom);

    const startInput = screen.getByLabelText('Start Date');
    const endInput = screen.getByLabelText('End Date');
    expect(startInput).toBeInTheDocument();
    expect(endInput).toBeInTheDocument();

    // Inverted range shows error warning
    fireEvent.change(startInput, { target: { value: '2026-11-20' } });
    fireEvent.change(endInput, { target: { value: '2026-11-10' } });

    expect(
      screen.getByText('Start date cannot be after end date')
    ).toBeInTheDocument();
  });

  it('displays empty state for users without projects or recurring series', async () => {
    vi.mocked(analyticsApi.getProjects).mockResolvedValue({
      total_projects: 0,
      projects: [],
    });
    vi.mocked(analyticsApi.getRecurring).mockResolvedValue({
      total_series: 0,
      active_series: 0,
      paused_or_stopped_series: 0,
      total_generated_occurrences: 0,
      completed_occurrences: 0,
      pending_due_occurrences: 0,
      future_occurrences: 0,
      skipped_occurrences: 0,
      eligible_due_occurrences: 0,
      adherence_rate: 0.0,
      frequency_breakdown: { daily: 0, weekly: 0, monthly: 0, yearly: 0, custom: 0 },
      schema_limitations_note: 'No series available.',
    });

    render(
      <MemoryRouter>
        <AnalyticsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No projects found')).toBeInTheDocument();
      expect(screen.getByText('No recurring series created')).toBeInTheDocument();
    });
  });

  it('handles partial API failures gracefully and displays error banner without crashing', async () => {
    vi.mocked(analyticsApi.getProjects).mockRejectedValue({
      response: { data: { detail: 'Database error in projects analytics.' } },
    });

    render(
      <MemoryRouter>
        <AnalyticsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Some analytics widgets could not be fully loaded/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Database error in projects analytics/i)
      ).toBeInTheDocument();
    });

    // Other successful widgets must still render
    expect(screen.getByText('Productivity Trends')).toBeInTheDocument();
    expect(screen.getByText('Recurring Task Insights')).toBeInTheDocument();
  });
});
