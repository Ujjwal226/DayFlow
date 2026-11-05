import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { RecurringTasksPage } from '../pages/RecurringTasksPage';
import { RecurringTaskDetailsPage } from '../pages/RecurringTaskDetailsPage';
import { RecurringTaskCard } from '../components/recurringTasks/RecurringTaskCard';
import { RecurrenceBadge } from '../components/recurringTasks/RecurrenceBadge';
import { RecurrenceRuleSelector } from '../components/recurringTasks/RecurrenceRuleSelector';
import { WeeklyScheduleSelector } from '../components/recurringTasks/WeeklyScheduleSelector';
import { SkipOccurrenceDialog } from '../components/recurringTasks/SkipOccurrenceDialog';
import { OccurrenceList } from '../components/recurringTasks/OccurrenceList';
import { recurringTasksApi } from '../api/recurringTasks';
import { categoriesApi } from '../api/categories';
import { projectsApi } from '../api/projects';
import { RecurringTask } from '../types/recurringTask';
import { Task } from '../types/task';

vi.mock('../api/recurringTasks');
vi.mock('../api/categories');
vi.mock('../api/projects');
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@example.com', display_name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

const mockRecurringSeries: RecurringTask = {
  id: 'series-123',
  user_id: 'user-1',
  title: 'Weekly Standup Meeting',
  description: 'Weekly team coordination and demo review',
  priority: 'HIGH',
  category_id: null,
  project_id: null,
  frequency: 'WEEKLY',
  interval: 1,
  start_date: '2026-05-04',
  end_date: '2026-12-31',
  max_occurrences: 52,
  weekdays: [0, 4], // Mon and Fri
  day_of_month: null,
  month_of_year: null,
  timezone: 'UTC',
  next_occurrence_date: '2026-05-08',
  occurrences_generated: 1,
  is_active: true,
  is_stopped: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockOccurrences: Task[] = [
  {
    id: 'task-occ-1',
    user_id: 'user-1',
    recurring_task_id: 'series-123',
    occurrence_date: '2026-05-04',
    occurrence_index: 1,
    title: 'Weekly Standup Meeting',
    description: 'Weekly team coordination and demo review',
    status: 'TODO',
    priority: 'HIGH',
    parent_task_id: null,
    category_id: null,
    project_id: null,
    start_date: '2026-05-04T00:00:00Z',
    due_date: '2026-05-04T00:00:00Z',
    completed_at: null,
    is_archived: false,
    is_overdue: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe('Recurring Tasks Frontend Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([]);
    vi.mocked(projectsApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    });
  });

  describe('Recurrence Components', () => {
    it('renders RecurrenceBadge correctly for daily, weekly, monthly and custom frequencies', () => {
      const { rerender } = render(<RecurrenceBadge frequency="DAILY" interval={1} />);
      expect(screen.getByText('Daily')).toBeInTheDocument();

      rerender(<RecurrenceBadge frequency="WEEKLY" interval={2} />);
      expect(screen.getByText('Every 2 weeks')).toBeInTheDocument();

      rerender(<RecurrenceBadge frequency="MONTHLY" interval={1} />);
      expect(screen.getByText('Monthly')).toBeInTheDocument();

      rerender(<RecurrenceBadge frequency="CUSTOM" interval={5} />);
      expect(screen.getByText('Every 5 days')).toBeInTheDocument();
    });

    it('handles weekday toggling in WeeklyScheduleSelector', () => {
      const handleChange = vi.fn();
      render(
        <WeeklyScheduleSelector
          selectedWeekdays={[0, 4]} // Monday, Friday
          onChange={handleChange}
        />
      );

      expect(screen.getByText('Mon')).toBeInTheDocument();
      expect(screen.getByText('Fri')).toBeInTheDocument();

      // Click Wednesday (value 2)
      fireEvent.click(screen.getByText('Wed'));
      expect(handleChange).toHaveBeenCalledWith([0, 2, 4]);
    });

    it('renders RecurrenceRuleSelector and switches frequency controls', () => {
      const handleFreqChange = vi.fn();
      const { rerender } = render(
        <RecurrenceRuleSelector
          frequency="DAILY"
          interval={1}
          weekdays={[0]}
          dayOfMonth={null}
          monthOfYear={null}
          onFrequencyChange={handleFreqChange}
          onIntervalChange={vi.fn()}
          onWeekdaysChange={vi.fn()}
          onDayOfMonthChange={vi.fn()}
          onMonthOfYearChange={vi.fn()}
        />
      );

      expect(screen.getByText('Repeat Every (Days)')).toBeInTheDocument();

      // Switch to Monthly
      rerender(
        <RecurrenceRuleSelector
          frequency="MONTHLY"
          interval={1}
          weekdays={[0]}
          dayOfMonth={15}
          monthOfYear={null}
          onFrequencyChange={handleFreqChange}
          onIntervalChange={vi.fn()}
          onWeekdaysChange={vi.fn()}
          onDayOfMonthChange={vi.fn()}
          onMonthOfYearChange={vi.fn()}
        />
      );

      expect(screen.getByText('Repeat Every (Months)')).toBeInTheDocument();
      expect(screen.getByText('Day of Month')).toBeInTheDocument();
    });

    it('renders RecurringTaskCard with series info and action handlers', () => {
      const handleEdit = vi.fn();
      const handlePause = vi.fn();
      const handleResume = vi.fn();
      const handleStop = vi.fn();
      const handleDelete = vi.fn();

      render(
        <BrowserRouter>
          <RecurringTaskCard
            series={mockRecurringSeries}
            onEdit={handleEdit}
            onPause={handlePause}
            onResume={handleResume}
            onStop={handleStop}
            onDelete={handleDelete}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Weekly Standup Meeting')).toBeInTheDocument();
      expect(screen.getByText(/Weekly team coordination/i)).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('2026-05-08')).toBeInTheDocument();

      // Click Pause button
      fireEvent.click(screen.getByText('Pause'));
      expect(handlePause).toHaveBeenCalledWith('series-123');

      // Click Stop button
      fireEvent.click(screen.getByText('Stop'));
      expect(handleStop).toHaveBeenCalledWith('series-123');
    });

    it('renders OccurrenceList with individual tasks', () => {
      render(
        <BrowserRouter>
          <OccurrenceList
            occurrences={mockOccurrences}
            total={1}
            page={1}
            totalPages={1}
            onPageChange={vi.fn()}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Weekly Standup Meeting')).toBeInTheDocument();
      expect(screen.getByText(/Occurrence Date: 2026-05-04/i)).toBeInTheDocument();
    });

    it('handles SkipOccurrenceDialog submission', async () => {
      const handleConfirm = vi.fn().mockResolvedValue(undefined);
      const handleClose = vi.fn();

      render(
        <SkipOccurrenceDialog
          isOpen={true}
          onClose={handleClose}
          onConfirm={handleConfirm}
          defaultDate="2026-05-08"
        />
      );

      expect(screen.getByText('Skip Next Occurrence')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2026-05-08')).toBeInTheDocument();

      fireEvent.change(screen.getByPlaceholderText(/e.g. Vacation/i), {
        target: { value: 'Holiday vacation' },
      });

      fireEvent.click(screen.getByText('Confirm Skip'));

      await waitFor(() => {
        expect(handleConfirm).toHaveBeenCalledWith('2026-05-08', 'Holiday vacation');
      });
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe('RecurringTasksPage View & Lifecycle', () => {
    it('renders the series list, empty state, and creates new recurring task', async () => {
      vi.mocked(recurringTasksApi.list).mockResolvedValue({
        items: [mockRecurringSeries],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      render(
        <BrowserRouter>
          <RecurringTasksPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Weekly Standup Meeting')).toBeInTheDocument();
      });

      expect(screen.getByText('Recurring Tasks & Scheduling')).toBeInTheDocument();
      expect(screen.getByText('1 series')).toBeInTheDocument();

      // Open creation modal
      const createBtn = screen.getAllByRole('button', { name: /Create Series/i })[0];
      fireEvent.click(createBtn);

      expect(screen.getByText('Create Recurring Task Series')).toBeInTheDocument();
    });

    it('renders empty state when no series match filters', async () => {
      vi.mocked(recurringTasksApi.list).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        total_pages: 0,
      });

      render(
        <BrowserRouter>
          <RecurringTasksPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No recurring tasks found')).toBeInTheDocument();
      });
    });
  });

  describe('RecurringTaskDetailsPage', () => {
    it('renders series details and occurrence history', async () => {
      vi.mocked(recurringTasksApi.get).mockResolvedValue(mockRecurringSeries);
      vi.mocked(recurringTasksApi.listOccurrences).mockResolvedValue({
        items: mockOccurrences,
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      });

      render(
        <MemoryRouter initialEntries={['/recurring-tasks/series-123']}>
          <Routes>
            <Route path="/recurring-tasks/:id" element={<RecurringTaskDetailsPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Weekly Standup Meeting' })).toBeInTheDocument();
      });

      expect(screen.getByText('Generated Occurrences')).toBeInTheDocument();
      expect(screen.getByText('1 tasks')).toBeInTheDocument();
      expect(screen.getByText(/Occurrence Date: 2026-05-04/i)).toBeInTheDocument();
      expect(screen.getByText('Skip Next')).toBeInTheDocument();
    });
  });
});
