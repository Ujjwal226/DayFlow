import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CalendarPage } from '../pages/CalendarPage';
import { calendarApi } from '../api/calendar';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    logout: vi.fn(),
    logoutAll: vi.fn(),
    isLoading: false,
    user: { display_name: 'Alex Developer', email: 'alex@example.com' },
  }),
}));

vi.mock('../api/calendar', () => ({
  calendarApi: {
    getFeed: vi.fn(),
  },
}));

describe('CalendarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders calendar layout and loads feed', async () => {
    (calendarApi.getFeed as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      items: [
        {
          id: 'item-1',
          type: 'event',
          title: 'Design Sprint',
          is_all_day: false,
          timezone: 'UTC',
          start_at: new Date().toISOString(),
          end_at: new Date(Date.now() + 3600000).toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      range_start: new Date().toISOString(),
      range_end: new Date().toISOString(),
      timezone: 'UTC',
      total: 1,
    });

    render(
      <MemoryRouter>
        <CalendarPage />
      </MemoryRouter>
    );

    // Initial loading indicator
    expect(screen.getByText('Loading your schedule...')).toBeInTheDocument();

    // After resolution
    await waitFor(() => {
      expect(screen.getByText('Design Sprint')).toBeInTheDocument();
    });

    // Check top navigation contains Calendar active pill
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Month')).toBeInTheDocument();
  });

  it('handles error state and allows retry', async () => {
    (calendarApi.getFeed as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('API Error')
    );

    render(
      <MemoryRouter>
        <CalendarPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load calendar feed. Please try again.')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});
