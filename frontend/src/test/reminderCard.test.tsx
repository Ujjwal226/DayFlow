import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReminderCard } from '../components/reminders/ReminderCard';
import { Reminder } from '../types/reminder';

describe('ReminderCard', () => {
  const mockReminder: Reminder = {
    id: 'rem-1',
    user_id: 'user-1',
    task_id: null,
    title: 'Review Quarterly Report',
    description: 'Ensure metrics match revenue forecast',
    scheduled_at: '2026-11-15T10:00:00Z',
    timezone: 'UTC',
    recurrence: 'DAILY',
    delivery_channels: 'IN_APP,EMAIL',
    status: 'PENDING',
    snoozed_until: null,
    created_at: '2026-11-10T10:00:00Z',
    updated_at: '2026-11-10T10:00:00Z',
  };

  it('renders reminder details correctly', () => {
    render(
      <ReminderCard
        reminder={mockReminder}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onComplete={vi.fn()}
        onDismiss={vi.fn()}
        onSnooze={vi.fn()}
      />
    );

    expect(screen.getByText('Review Quarterly Report')).toBeInTheDocument();
    expect(screen.getByText(/Ensure metrics match revenue forecast/)).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText(/daily/i)).toBeInTheDocument();
  });

  it('triggers complete and dismiss action callbacks', () => {
    const onComplete = vi.fn();
    const onDismiss = vi.fn();

    render(
      <ReminderCard
        reminder={mockReminder}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onComplete={onComplete}
        onDismiss={onDismiss}
        onSnooze={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Complete'));
    expect(onComplete).toHaveBeenCalledWith('rem-1');

    fireEvent.click(screen.getByText('Dismiss'));
    expect(onDismiss).toHaveBeenCalledWith('rem-1');
  });
});

