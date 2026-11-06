import { describe, it, expect, vi, beforeEach } from 'vitest';
import { calendarApi } from '../api/calendar';
import { apiClient } from '../api/client';
import { CalendarFeedResponse } from '../types/calendar';

vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('calendarApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /calendar/feed with correctly formatted query params', async () => {
    const mockResponse: CalendarFeedResponse = {
      items: [],
      range_start: '2026-11-01T00:00:00Z',
      range_end: '2026-11-30T00:00:00Z',
      timezone: 'UTC',
      total: 0,
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: mockResponse,
    });

    const result = await calendarApi.getFeed({
      start: '2026-11-01T00:00:00Z',
      end: '2026-11-30T00:00:00Z',
      timezone: 'America/New_York',
      include_tasks: true,
      include_events: true,
      status: 'TODO',
    });

    expect(apiClient.get).toHaveBeenCalledTimes(1);
    const [url, config] = (apiClient.get as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('/calendar/feed');
    const params = config.params as URLSearchParams;
    expect(params.get('start')).toBe('2026-11-01T00:00:00Z');
    expect(params.get('end')).toBe('2026-11-30T00:00:00Z');
    expect(params.get('timezone')).toBe('America/New_York');
    expect(params.get('include_tasks')).toBe('true');
    expect(params.get('include_events')).toBe('true');
    expect(params.get('status')).toBe('TODO');
    expect(result).toEqual(mockResponse);
  });
});

