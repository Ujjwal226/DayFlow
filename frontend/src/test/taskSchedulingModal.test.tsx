import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskSchedulingModal } from '../components/calendar/TaskSchedulingModal';
import { tasksApi } from '../api/tasks';

vi.mock('../api/tasks', () => ({
  tasksApi: {
    listTasks: vi.fn(),
  },
}));

describe('TaskSchedulingModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads tasks, allows selection and schedules time block', async () => {
    (tasksApi.listTasks as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      items: [
        {
          id: 'task-101',
          title: 'Review Financial Statements',
          status: 'TODO',
          priority: 'HIGH',
          due_date: '2026-11-25T18:00:00Z',
        },
      ],
      total: 1,
    });

    const onSchedule = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    render(
      <TaskSchedulingModal
        isOpen={true}
        prefillDate={new Date(2026, 10, 18, 9, 0)}
        onClose={onClose}
        onSchedule={onSchedule}
      />
    );

    // Verify task is loaded and listed
    await waitFor(() => {
      expect(screen.getByText('Review Financial Statements')).toBeInTheDocument();
    });

    // Select the task
    fireEvent.click(screen.getByText('Review Financial Statements'));

    expect(screen.getByText('Selected: Review Financial Statements')).toBeInTheDocument();

    // Click schedule button
    const submitBtn = screen.getByText('Schedule Time Block');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSchedule).toHaveBeenCalledWith(
        expect.objectContaining({
          task_id: 'task-101',
        })
      );
    });
  });
});

