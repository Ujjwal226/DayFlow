# Focus & Pomodoro Productivity Module (Stage 3F)

## Overview

The Focus & Pomodoro module in DayFlow provides an integrated deep-work productivity timer connected with tasks, projects, dashboard analytics, user goals, and notification systems.

Unlike naive timer implementations that rely strictly on client-side `setInterval` or in-memory variables, DayFlow’s Focus system is backed by an **authoritative, persisted timestamp model**. The backend database maintains the authoritative state of all sessions, ensuring accurate elapsed and remaining calculations regardless of tab switching, browser restarts, throttling, or offline gaps.

---

## 1. Database Architecture & Concurrency Strategy

### Tables

1. **`focus_sessions`**
   - `id`: UUID primary key.
   - `user_id`: UUID foreign key to `users.id` (multi-tenant partition).
   - `task_id`: Optional UUID foreign key to `tasks.id` (set null on delete).
   - `project_id`: Optional UUID foreign key to `projects.id` (set null on delete).
   - `session_type`: `FOCUS`, `SHORT_BREAK`, or `LONG_BREAK`.
   - `status`: `ACTIVE`, `PAUSED`, `COMPLETED`, or `ABANDONED`.
   - `planned_duration_seconds`: Target duration when session was initiated.
   - `actual_duration_seconds`: Total active elapsed time logged upon completion or abandonment.
   - `accumulated_pause_seconds`: Sum of all paused durations.
   - `started_at`: UTC timestamp when timer started.
   - `paused_at`: UTC timestamp of the most recent pause (null when active).
   - `completed_at`: UTC timestamp when session concluded.
   - `notes`: Optional user notes.

2. **`focus_preferences`**
   - Configures user-specific timer defaults:
     - `focus_duration_minutes` (default: 25)
     - `short_break_duration_minutes` (default: 5)
     - `long_break_duration_minutes` (default: 15)
     - `long_break_interval` (default: 4 sessions)
     - `daily_goal_minutes` (default: 120 minutes)
     - `auto_start_breaks` (default: false)
     - `auto_start_focus` (default: false)
     - `sound_enabled` (default: true)
     - `browser_notifications_enabled` (default: true)

### Concurrency & Uniqueness Enforcement

- **Partial Unique Index:**
  To guarantee that concurrent requests cannot create multiple `ACTIVE` or `PAUSED` sessions for the same user, a database-level partial unique index is enforced:
  ```sql
  CREATE UNIQUE INDEX uq_focus_sessions_user_active_or_paused
  ON focus_sessions (user_id)
  WHERE status IN ('ACTIVE', 'PAUSED');
  ```
- **Application-Level Conflict Catching:**
  `start_session` performs row-level locking (`with_for_update()`) where supported, and wraps session insertion in an `IntegrityError` handler that rolls back the transaction and translates unique index violations into a clean `409 Conflict` HTTP response:
  ```json
  {
    "detail": "An active or paused focus session is already running. Complete or abandon it first."
  }
  ```

### Alembic Migration
- Migration `c3d4e5f6a7b8` (`create_focus_tables.py`) applies both tables, partial unique index `uq_focus_sessions_user_active_or_paused`, and composite indexes.
- Parent revision: `b2c3d4e5f6a7`. Verified single Alembic head.

---

## 2. Authoritative Timestamp Calculations

To prevent timer drift, throttling during background tabs, or loss of state on refresh, the remaining and elapsed calculations follow strict timestamp arithmetic:

1. **When Status is `PAUSED`:**
   $$\text{effective\_elapsed} = (\text{paused\_at} - \text{started\_at}) - \text{accumulated\_pause\_seconds}$$

2. **When Status is `ACTIVE`:**
   $$\text{effective\_elapsed} = (\text{now()} - \text{started\_at}) - \text{accumulated\_pause\_seconds}$$

3. **Remaining Duration:**
   $$\text{remaining\_seconds} = \max(0, \text{planned\_duration\_seconds} - \text{effective\_elapsed})$$

4. **Expiration Handling:**
   When $\text{remaining\_seconds} \le 0$, the session is expired. Any query to `GET /focus/active` or `POST /focus/start` detects expiration and cleanly completes the session, setting `actual_duration_seconds = planned_duration_seconds` and triggering Stage 3E in-app notifications.

---

## 3. API Endpoints

All endpoints are scoped under `/api/v1/focus` and require JWT authentication:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/focus/active` | Returns active or paused session with remaining seconds, or `null`. |
| `POST` | `/api/v1/focus/start` | Starts a new session. Validates tenancy and rejects with `409 Conflict` if an active session exists. |
| `POST` | `/api/v1/focus/sessions/{id}/pause` | Pauses an active session and stores `paused_at`. |
| `POST` | `/api/v1/focus/sessions/{id}/resume` | Resumes a paused session, incrementing `accumulated_pause_seconds`. |
| `POST` | `/api/v1/focus/sessions/{id}/complete` | Idempotently completes session as `COMPLETED`, records actual duration, and creates Stage 3E in-app notification. |
| `POST` | `/api/v1/focus/sessions/{id}/abandon` | Concludes session as `ABANDONED`. Excludes actual time from completed focus analytics. |
| `POST` | `/api/v1/focus/sessions/{id}/skip` | Skips current session (marks `ABANDONED` with 0 actual seconds) and starts next session in Pomodoro cycle. |
| `GET` | `/api/v1/focus/sessions/{id}` | Retrieves session details with strict user ownership validation. |
| `GET` | `/api/v1/focus/history` | Returns recent sessions with task and project metadata. |
| `GET` | `/api/v1/focus/preferences` | Fetches user's timer and browser notification preferences. |
| `PATCH`| `/api/v1/focus/preferences` | Updates user's timer and notification preferences. |
| `GET` | `/api/v1/focus/analytics` | Returns timezone-aware daily summary, 7-day trend, and task/project breakdowns. |

---

## 4. Notifications & Browser Permission Handling

- **Preference Persistence:** Stored in `focus_preferences.browser_notifications_enabled` (boolean).
- **User Permission Request:** Browser notification permission (`Notification.requestPermission()`) is only triggered upon explicit user toggle in the settings modal.
- **Graceful Fallback:** If browser permission is denied or unavailable, the UI displays `(Blocked in browser settings)` without crashing.
- **In-App Integration:** Stage 3E in-app notifications are created via `NotificationRepository` upon successful session completion. Idempotent complete calls prevent duplicate notification spam.

---

## 5. Analytics Coverage

- **Timezone Awareness:** Takes user timezone query parameter (defaulting to UTC) and slices 24-hour daily bounds ($00:00:00$ to $23:59:59.999999$) locally before converting to UTC for database queries.
- **Strict Metric Isolation:** Only counts `status == 'COMPLETED'` and `session_type == 'FOCUS'`. Abandoned sessions, cancelled sessions, and breaks are strictly excluded.
- **Average Duration & Streaks:** Computes average completed session duration and user streak consistency.
