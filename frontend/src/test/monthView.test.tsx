import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MonthView } from '../components/calendar/MonthView';
import { CalendarFeedItem } from '../types/calendar';

describe('MonthView', () => {
  const currentDate = new Date(2026, 10, 15); // Nov 15, 2026

  const mockItems: CalendarFeedItem[] = [
    {
      id: 'event-1',
      type: 'event',
      title: 'Board Meeting',
      is_all_day: false,
      timezone: 'UTC',
      start_at: new Date(2026, 10, 15, 10, 0).toISOString(),
      end_at: new Date(2026, 10, 15, 11, 0).toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'task-1',
      type: 'task_deadline',
      title: 'Submit Taxes',
      status: 'TODO',
      priority: 'HIGH',
      due_date: new Date(2026, 10, 15, 17, 0).toISOString(),
      is_overdue: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  it('renders all weekday headers and days', () => {
    render(
      <MonthView
        currentDate={currentDate}
        items={mockItems}
        onSelectDate={vi.fn()}
      />
    );

    expect(screen.getByText('Mon')).toBeInTheDocument();
    expect(screen.getByText('Fri')).toBeInTheDocument();
    expect(screen.getByText('Sun')).toBeInTheDocument();
  });

  it('renders event and task pills on the corresponding day', () => {
    render(
      <MonthView
        currentDate={currentDate}
        items={mockItems}
        onSelectDate={vi.fn()}
      />
    );

    expect(screen.getByText('Board Meeting')).toBeInTheDocument();
    expect(screen.getByText('Submit Taxes')).toBeInTheDocument();
  });

  it('calls onSelectDate when a date cell is clicked', () => {
    const onSelectDate = vi.fn();
    render(
      <MonthView
        currentDate={currentDate}
        items={mockItems}
        onSelectDate={onSelectDate}
      />
    );

    fireEvent.click(screen.getByText('Board Meeting').closest('div[class*="min-h-"]')!);
    expect(onSelectDate).toHaveBeenCalled();
  });
});
