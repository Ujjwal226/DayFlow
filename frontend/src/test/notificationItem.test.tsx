import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NotificationItem } from '../components/notifications/NotificationItem';
import { Notification } from '../types/notification';

describe('NotificationItem', () => {
  const mockNotification: Notification = {
    id: 'notif-1',
    user_id: 'user-1',
    reminder_id: 'rem-1',
    task_id: null,
    title: 'Upcoming Deadline',
    message: 'Your project milestone is due tomorrow.',
    type: 'REMINDER',
    is_read: false,
    read_at: null,
    created_at: '2026-11-10T14:30:00Z',
  };

  it('renders notification title and message', () => {
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkAsRead={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('Upcoming Deadline')).toBeInTheDocument();
    expect(screen.getByText('Your project milestone is due tomorrow.')).toBeInTheDocument();
    expect(screen.getByText('Mark Read')).toBeInTheDocument();
  });

  it('triggers mark as read callback when clicked', () => {
    const onMarkAsRead = vi.fn();
    render(
      <NotificationItem
        notification={mockNotification}
        onMarkAsRead={onMarkAsRead}
        onDelete={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Mark Read'));
    expect(onMarkAsRead).toHaveBeenCalledWith('notif-1');
  });

  it('hides Mark Read button when notification is already read', () => {
    render(
      <NotificationItem
        notification={{ ...mockNotification, is_read: true }}
        onMarkAsRead={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.queryByText('Mark Read')).not.toBeInTheDocument();
  });
});

