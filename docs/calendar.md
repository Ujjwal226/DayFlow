# DayFlow — Calendar & Scheduling Architecture and Reference

## 1. CalendarEvent Purpose & Overview

`CalendarEvent` provides DayFlow with a dedicated representation for scheduled appointments, time allocations, meetings, and all-day blocks.

### Distinction Between Tasks and Calendar Events
- **Tasks (`Task`)**:
  - Actionable deliverables and to-do items.
  - Track lifecycle states (`TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), priority levels, subtasks, projects, categories, and tags.
  - Have optional deadlines (`due_date`) and earliest start times (`start_date`).
  - Represent execution windows and deadlines, not fixed calendar bookings.
- **Calendar Events (`CalendarEvent`)**:
  - Fixed time allocations and scheduled blocks on a personal calendar.
  - Have definite durations and boundaries.
  - May be standalone (meetings, focus time) or linked to a task (`task_id`) to support time-blocking workflows.

---

## 2. Date and Time Representation

DayFlow supports two mutually exclusive calendar event formats enforced at both database check constraint and Pydantic validation levels:

### A. Timed Events (`is_all_day = false`)
- `start_at`: UTC `DateTime(timezone=True)`.
- `end_at`: UTC `DateTime(timezone=True)`.
- `end_at` must be strictly after `start_at`.
- All-day date fields (`start_date`, `end_date`) must be `NULL`.
- `timezone`: Preserves the user's original IANA timezone identifier (e.g., `America/New_York`, `UTC`, `Asia/Kolkata`).

### B. All-Day Events (`is_all_day = true`)
- `start_date`: SQL `Date` (`YYYY-MM-DD`).
- `end_date`: SQL `Date` (`YYYY-MM-DD`, exclusive boundary).
- `end_date` must be strictly after `start_date`.
- Timed timestamp fields (`start_at`, `end_at`) must be `NULL`.
- Example: an event from Nov 10 through Nov 12 has `start_date = 2026-11-10` and `end_date = 2026-11-13`.

---

## 3. Unified Calendar Feed (`GET /api/v1/calendar/feed`)

The unified calendar feed combines calendar events and task deadlines into a single chronologically sorted feed for a given time window.

### A. Endpoint & Parameters
- `start`: Required ISO-8601 datetime with timezone offset (e.g. `2026-11-01T00:00:00Z`).
- `end`: Required ISO-8601 datetime with timezone offset.
- `timezone`: Optional IANA timezone identifier (defaults to `UTC`).
- `include_tasks`: Boolean, defaults to `true`.
- `include_events`: Boolean, defaults to `true`.
- `project_id`: Optional UUID filter.
- `category_id`: Optional UUID filter.
- `status`: Optional task status filter (`TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`).
- `priority`: Optional task priority filter (`LOW`, `MEDIUM`, `HIGH`, `URGENT`).
- `recurring_only`: Optional boolean filter for recurring occurrences.

### B. Range & Overlap Semantics
- Half-open query window: `[start, end)`.
- Maximum query window: **93 days** (approx. 3 calendar months). Requests exceeding 93 days are rejected with `422 Unprocessable Entity`.
- **Timed Events**: Included if `event.start_at < range_end_utc AND event.end_at > range_start_utc` (captures events starting before the range that extend into it).
- **All-Day Events**: Included if `event.start_date < local_end_date AND event.end_date > local_start_date` based on the requested timezone.
- **Task Deadlines**: Included if `task.due_date >= range_start_utc AND task.due_date < range_end_utc`. Tasks without a due date are omitted from the calendar feed.

### C. Recurring Task Occurrences
- Recurring occurrences are already materialized as physical `Task` rows in DayFlow.
- The calendar feed does **not** generate new recurring occurrences. It queries existing materialized occurrences.
- Handled via `task_deadline` items containing `recurring_task_id`, `occurrence_date`, and `occurrence_index`.
- No duplicate occurrences are generated or returned.

---

## 4. Frontend Calendar Architecture (Phase 3)

The internal calendar frontend is implemented using React 18, TypeScript, and Tailwind CSS without third-party calendar libraries:

### A. Component Hierarchy
- `CalendarPage.tsx`: Main page component with top application header, navigation, view state, date calculation, race-condition guarded API fetching, error handling with retry, and loading state.
- `CalendarToolbar.tsx`: Toolbar providing Previous/Next period navigation, Today shortcut, dynamic heading formatted by view, and Month/Week/Day mode toggle buttons.
- `MonthView.tsx`: 7-column calendar grid supporting 5 or 6 week months, displaying trailing and leading days, today indicator, active cell highlight, compact item pills, and overflow counter (`+N more`). Clicking a cell navigates to Day View for that date.
- `WeekView.tsx`: 7-day multi-column timeline with an upper All-Day / Due section and a 24-hour vertical scroll grid with hourly slot placement.
- `DayView.tsx`: Single-day schedule with date header, all-day items, and detailed hourly timeline.
- `CalendarItemPill.tsx`: Unified rendering pill distinguishing standalone calendar events, task-linked time blocks, and task deadlines with status and priority indicators.

### B. Date and Timezone Handling
- The browser's local timezone (`Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'`) is passed with every feed request.
- Local time formatting displays events and task deadlines in the user's active timezone without UTC date shifting.

---

## 5. Scope Boundaries & Planned Phase 4 Work

- **In Scope for Phase 3**: Frontend calendar views (Month, Week, Day), unified feed API client, view switching, navigation, loading/error states, and unit tests.
- **Deferred to Phase 4**: Interactive event creation & editing modal, task scheduling modal, and advanced filter drawer.
- **Deferred to Phase 5+**: Google Calendar OAuth2, bidirectional synchronization engine.
