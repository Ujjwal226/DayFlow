import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CalendarToolbar } from '../components/calendar/CalendarToolbar';

describe('CalendarToolbar', () => {
  const defaultDate = new Date(2026, 10, 15); // Nov 15, 2026

  it('renders period label correctly for month view', () => {
    render(
      <CalendarToolbar
        currentDate={defaultDate}
        viewMode="month"
        onViewModeChange={vi.fn()}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onToday={vi.fn()}
        onNewEvent={vi.fn()}
        onScheduleTask={vi.fn()}
        onOpenFilters={vi.fn()}
        activeFilterCount={0}
      />
    );

    expect(screen.getByText('November 2026')).toBeInTheDocument();
  });

  it('invokes navigation callbacks when buttons clicked', () => {
    const onPrev = vi.fn();
    const onNext = vi.fn();
    const onToday = vi.fn();
    const onViewModeChange = vi.fn();

    render(
      <CalendarToolbar
        currentDate={defaultDate}
        viewMode="month"
        onViewModeChange={onViewModeChange}
        onPrev={onPrev}
        onNext={onNext}
        onToday={onToday}
        onNewEvent={vi.fn()}
        onScheduleTask={vi.fn()}
        onOpenFilters={vi.fn()}
        activeFilterCount={0}
      />
    );

    fireEvent.click(screen.getByTitle('Jump to today'));
    expect(onToday).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTitle('Previous period'));
    expect(onPrev).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTitle('Next period'));
    expect(onNext).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Week'));
    expect(onViewModeChange).toHaveBeenCalledWith('week');

    fireEvent.click(screen.getByText('Day'));
    expect(onViewModeChange).toHaveBeenCalledWith('day');
  });
});
