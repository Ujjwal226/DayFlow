import { apiClient } from './client';
import {
  CalendarEventCreatePayload,
  CalendarEventItem,
  CalendarEventUpdatePayload,
  CalendarFeedQuery,
  CalendarFeedResponse,
  ScheduleTaskPayload,
} from '../types/calendar';

export const calendarApi = {
  /**
   * Fetch unified calendar feed of events and task deadlines.
   */
  getFeed: async (query: CalendarFeedQuery): Promise<CalendarFeedResponse> => {
    const params = new URLSearchParams();
    params.append('start', query.start);
    params.append('end', query.end);

    if (query.timezone) params.append('timezone', query.timezone);
    if (query.include_tasks !== undefined) params.append('include_tasks', String(query.include_tasks));
    if (query.include_events !== undefined) params.append('include_events', String(query.include_events));
    if (query.project_id) params.append('project_id', query.project_id);
    if (query.category_id) params.append('category_id', query.category_id);
    if (query.status) params.append('status', query.status);
    if (query.priority) params.append('priority', query.priority);
    if (query.recurring_only !== undefined) params.append('recurring_only', String(query.recurring_only));

    const response = await apiClient.get<CalendarFeedResponse>('/calendar/feed', {
      params,
    });
    return response.data;
  },

  /**
   * Create a new standalone or task-associated calendar event.
   */
  createEvent: async (payload: CalendarEventCreatePayload): Promise<CalendarEventItem> => {
    const response = await apiClient.post<CalendarEventItem>('/calendar/events', payload);
    return response.data;
  },

  /**
   * Retrieve a specific calendar event.
   */
  getEvent: async (eventId: string): Promise<CalendarEventItem> => {
    const response = await apiClient.get<CalendarEventItem>(`/calendar/events/${eventId}`);
    return response.data;
  },

  /**
   * Update fields of an existing calendar event.
   */
  updateEvent: async (eventId: string, payload: CalendarEventUpdatePayload): Promise<CalendarEventItem> => {
    const response = await apiClient.put<CalendarEventItem>(`/calendar/events/${eventId}`, payload);
    return response.data;
  },

  /**
   * Delete a calendar event.
   */
  deleteEvent: async (eventId: string): Promise<void> => {
    await apiClient.delete(`/calendar/events/${eventId}`);
  },

  /**
   * Schedule a task into a calendar time block.
   */
  scheduleTask: async (payload: ScheduleTaskPayload): Promise<CalendarEventItem> => {
    const response = await apiClient.post<CalendarEventItem>('/calendar/events/schedule-task', payload);
    return response.data;
  },
};
