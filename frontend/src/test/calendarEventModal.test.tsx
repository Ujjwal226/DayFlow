import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CalendarEventModal } from '../components/calendar/CalendarEventModal';
import { CalendarEventItem } from '../types/calendar';

describe('CalendarEventModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create mode with prefilled date and validates title', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    render(
      <CalendarEventModal
        isOpen={true}
        event={null}
        prefillDate={new Date(2026, 10, 15)}
        onClose={onClose}
        onSave={onSave}
      />
    );

    expect(screen.getByText('Create Calendar Event')).toBeInTheDocument();

    // Fill title
    const titleInput = screen.getByPlaceholderText('Meeting with product team');
    fireEvent.change(titleInput, { target: { value: 'Sprint Planning' } });

    // Click submit
    const submitBtn = screen.getByText('Create Event');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
    });
  });

  it('renders edit mode for existing event and calls delete', async () => {
    const onSave = vi.fn();
    const onDelete = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    const existingEvent: CalendarEventItem = {
      id: 'event-456',
      type: 'event',
      title: 'Quarterly Review',
      is_all_day: true,
      timezone: 'UTC',
      start_date: '2026-11-20',
      end_date: '2026-11-22',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(
      <CalendarEventModal
        isOpen={true}
        event={existingEvent}
        onClose={onClose}
        onSave={onSave}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText('Edit Calendar Event')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Quarterly Review')).toBeInTheDocument();

    // Click delete -> shows confirmation
    const deleteBtn = screen.getByText('Delete Event');
    fireEvent.click(deleteBtn);

    expect(screen.getByText('Confirm delete?')).toBeInTheDocument();
    const confirmBtn = screen.getByText('Yes, Delete');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith('event-456');
    });
  });
});

