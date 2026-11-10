# Reminders and Notifications Architecture Documentation

## Overview

Stage 3E introduces a production-ready, multi-tenant reminders and notifications system for DayFlow. It provides users with in-app alerts, scheduling controls, task linkage, recurrence options, configurable notification preferences, and reliable transactional email delivery with exponential backoff retries.

---

## 1. Data Models & Database Schema

The implementation is backed by an Alembic migration (`b2c3d4e5f6a7`) creating four tables:

### A. `reminders`
- `id`: UUID Primary Key.
- `user_id`: UUID Foreign Key to `users.id` (CASCADE delete).
- `task_id`: UUID Nullable Foreign Key to `tasks.id` (SET NULL delete).
- `title`: String(255), reminder headline.
- `description`: Text, optional details.
- `scheduled_at`: DateTime(timezone=True), UTC execution time.
- `timezone`: String(64), original user timezone (defaults to "UTC").
- `recurrence`: String(32), recurrence cadence (`NONE`, `DAILY`, `WEEKLY`, `MONTHLY`).
- `delivery_channels`: String(64), comma-separated list of enabled channels (`IN_APP`, `EMAIL`, or `IN_APP,EMAIL`).
- `status`: String(32), status enum (`PENDING`, `SENT`, `COMPLETED`, `DISMISSED`, `SNOOZED`).
- `snoozed_until`: DateTime(timezone=True), nullable UTC time if snoozed.
- `created_at`, `updated_at`: DateTime(timezone=True) timestamps.

### B. `notifications`
- `id`: UUID Primary Key.
- `user_id`: UUID Foreign Key to `users.id` (CASCADE delete).
- `reminder_id`: UUID Nullable Foreign Key to `reminders.id` (SET NULL).
- `task_id`: UUID Nullable Foreign Key to `tasks.id` (SET NULL).
- `title`: String(255).
- `message`: Text.
- `type`: String(32) (`REMINDER`, `TASK_DUE`, `OVERDUE`, `SYSTEM`).
- `is_read`: Boolean (defaults to `false`).
- `read_at`: DateTime(timezone=True), timestamp when marked read.
- `created_at`: DateTime(timezone=True).

### C. `email_deliveries` (Outbox Pattern)
- `id`: UUID Primary Key.
- `user_id`: UUID Foreign Key to `users.id` (CASCADE delete).
- `notification_id`: UUID Nullable Foreign Key to `notifications.id` (SET NULL).
- `recipient_email`: String(255).
- `subject`: String(255).
- `body`: Text.
- `status`: String(32) (`PENDING`, `SENT`, `FAILED`).
- `attempts`: Integer (retry attempt counter).
- `last_attempt_at`: DateTime(timezone=True).
- `next_retry_at`: DateTime(timezone=True), timestamp for backoff retry.
- `error_message`: Text, diagnostics on delivery failure.
- `created_at`: DateTime(timezone=True).

### D. `notification_preferences`
- `id`: UUID Primary Key.
- `user_id`: UUID Unique Foreign Key to `users.id` (CASCADE delete).
- `in_app_enabled`: Boolean (default `true`).
- `email_enabled`: Boolean (default `true`).
- `task_reminders_enabled`: Boolean (default `true`).
- `due_date_reminders_enabled`: Boolean (default `true`).
- `overdue_reminders_enabled`: Boolean (default `true`).
- `preferred_timezone`: String(64) (default `"UTC"`).
- `quiet_hours_enabled`: Boolean (default `false`).
- `quiet_hours_start`: String(5) (e.g. `"22:00"`).
- `quiet_hours_end`: String(5) (e.g. `"08:00"`).
- `updated_at`: DateTime(timezone=True).

---

## 2. Background Scheduler & Delivery Semantics

### Realistic Delivery Guarantees: At-Least-Once Delivery
DayFlow provides **at-least-once** delivery semantics for transactional email notifications (not exactly-once).
- **Why Exactly-Once is Impossible in SMTP**:
  Email transfer over SMTP constitutes an inherently distributed, non-transactional boundary. In any system where an application sends an email across a network socket and subsequently records that success in an ACID database:
  1. The remote SMTP server accepts the message (250 OK).
  2. If the application server loses power, crashes, or the database transaction fails before committing `status = 'SENT'`, the database still contains `status = 'PENDING'`.
  3. Upon worker restart or recovery, the scheduler detects the pending delivery and re-dispatches it.
  Claiming "exactly-once" delivery across an SMTP boundary is mathematically and architecturally false. DayFlow embraces robust **at-least-once** delivery with duplicate-risk mitigation.

### Duplicate Risk Mitigation: Deterministic RFC 5322 Message-ID
To mitigate the impact of the crash window:
- Every email delivery in DayFlow generates a deterministic Message-ID derived from its persistent outbox record:
  $$\text{Message-ID} = \langle \text{delivery\_id} @ \text{dayflow.app} \rangle$$
- Deterministic `Message-ID` values help identify retransmissions across logs and downstream MTAs, but do not guarantee that third-party SMTP providers or receiving mailboxes will deduplicate them.

### Multi-Worker Concurrency & Row Locking
- The scheduler employs **PostgreSQL Row-Level Locking** via `SELECT ... FOR UPDATE SKIP LOCKED` to protect concurrent database claims.
- When multiple backend processes or worker threads run concurrently, each process atomically locks and claims distinct pending rows.
- Other workers skip locked rows without blocking, preventing concurrent workers from processing or transmitting the same email or reminder twice.
- *Testing Limitation Note*: Actual multi-process PostgreSQL locking has not yet been verified through a live PostgreSQL concurrency test (test fixtures execute on SQLite in-memory).

### Worker Crash Recovery
- If a worker crashes mid-run, its database connection drops, releasing any active row locks.
- Uncommitted deliveries remain `status = 'PENDING'` with their scheduled `next_retry_at`.
- Upon service restart or in the next scheduler cycle, the surviving worker automatically picks up and processes pending deliveries, guaranteeing that deliveries are never permanently stranded.

### Retry Semantics & Bounded Exponential Backoff
- When an email delivery fails (due to network timeout, DNS failure, or SMTP rejection), the scheduler catches the exception and schedules a retry with exponential backoff:
  $$\text{delay} = 30 \times 2^{(\text{attempts}-1)} \text{ seconds}$$
  - Attempt 1: 30s
  - Attempt 2: 60s
  - Attempt 3: 120s
  - Attempt 4: 240s
- When `attempts >= 5`, the record enters a terminal `FAILED` status, preventing infinite retry loops.

---

## 3. REST API Endpoints

### Reminders (`/api/v1/reminders`)
- `POST /api/v1/reminders`: Create a reminder (supports date/time, recurrence, task linkage).
- `GET /api/v1/reminders`: List current user's reminders with status & task filter.
- `GET /api/v1/reminders/{id}`: Get a reminder by ID with tenant security check.
- `PATCH /api/v1/reminders/{id}`: Update title, description, time, or channels.
- `POST /api/v1/reminders/{id}/snooze`: Snooze for N minutes.
- `POST /api/v1/reminders/{id}/complete`: Mark reminder as completed.
- `POST /api/v1/reminders/{id}/dismiss`: Dismiss reminder.
- `DELETE /api/v1/reminders/{id}`: Permanently delete a reminder.

### Notifications (`/api/v1/notifications`)
- `GET /api/v1/notifications`: List notifications with unread/read filter.
- `GET /api/v1/notifications/unread-count`: Returns `{ "unread_count": N }`.
- `PATCH /api/v1/notifications/{id}/read`: Mark notification as read.
- `POST /api/v1/notifications/mark-all-read`: Mark all notifications as read.
- `DELETE /api/v1/notifications/{id}`: Delete a notification.

### Notification Preferences (`/api/v1/notification-preferences`)
- `GET /api/v1/notification-preferences`: Get user preferences or defaults.
- `PATCH /api/v1/notification-preferences`: Update preferences (quiet hours, channels, alerts).

---

## 4. Frontend UI Components & Pages

1. **`NotificationBell` (`components/notifications/NotificationBell.tsx`)**:
   - Bell icon with reactive unread counter badge.
   - Dropdown showing recent notifications with quick mark-as-read and dismiss actions.
   - Direct navigation to `/notifications` and `/settings/notifications`.
2. **`NotificationItem` (`components/notifications/NotificationItem.tsx`)**:
   - Renders notification details, relative time, and status indicator.
3. **`ReminderCard` (`components/reminders/ReminderCard.tsx`)**:
   - Displays scheduled time, snoozed state, recurrence badge, and delivery channels.
   - Quick actions: complete, dismiss, snooze menu (15m, 1h, 1d), edit, and delete.
4. **`ReminderModal` (`components/reminders/ReminderModal.tsx`)**:
   - Create or edit reminders with recurrence options and optional task selection.
5. **Pages**:
   - `/reminders` (`RemindersPage.tsx`): Overview of all reminders with status filters.
   - `/notifications` (`NotificationsPage.tsx`): Full history with unread filters and bulk read actions.
   - `/settings/notifications` (`NotificationPreferencesPage.tsx`): Channel and quiet hours configuration.

---

## 5. SMTP Configuration

In `.env`, configure the following settings:

```env
EMAIL_PROVIDER=smtp
EMAIL_FROM=notifications@dayflow.app
EMAIL_FROM_NAME="DayFlow App"
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_USE_TLS=True
SMTP_USE_SSL=False
```

When `EMAIL_PROVIDER=development` (default), emails are logged clearly to the console simulator without requiring external network connections.
