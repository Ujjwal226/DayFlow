# DayFlow — Task Management Architecture & API Documentation

## 1. Overview

DayFlow Stage 2 introduces **Advanced Personal Task Management**, providing authenticated users with a complete system to create, organize, schedule, filter, search, archive, and manage personal tasks with strict multi-user isolation.

---

## 2. Database Model: `tasks`

Implemented via SQLAlchemy 2.0 in `backend/app/models/task.py`:

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | `UUID` | No | Primary key, automatically generated (`uuid.uuid4`) |
| `user_id` | `UUID` | No | Foreign Key (`users.id`, `ON DELETE CASCADE`), indexed |
| `title` | `VARCHAR(200)` | No | Task title, trimmed, max 200 chars |
| `description` | `TEXT` | Yes | Detailed task content |
| `status` | `Enum (task_status)` | No | `TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `priority` | `Enum (task_priority)` | No | `LOW`, `MEDIUM`, `HIGH`, `URGENT` |
| `start_date` | `TIMESTAMP WITH TIME ZONE` | Yes | Scheduled start time |
| `due_date` | `TIMESTAMP WITH TIME ZONE` | Yes | Task deadline (indexed) |
| `completed_at` | `TIMESTAMP WITH TIME ZONE` | Yes | Timestamp set on completion, cleared on reopen |
| `is_archived` | `BOOLEAN` | No | Active vs archived flag, default `False` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | No | Timestamp created (`server_default=now()`) |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | No | Timestamp updated (`server_default=now()`) |

### Composite Indexes:
- `ix_tasks_user_id_status`: Fast filtered queries by user and status.
- `ix_tasks_user_id_is_archived`: Efficient segregation of active vs. archived tasks.
- `ix_tasks_user_id_due_date`: High-performance sorting and date-range queries.

---

## 3. API Endpoints (`/api/v1/tasks`)

All task endpoints require an active JWT Bearer token in the `Authorization` header and enforce strict multi-user isolation.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/tasks` | Create a new task (auto-scoped to `current_user.id`) |
| `GET` | `/api/v1/tasks` | List paginated tasks with search, filters, and sort options |
| `GET` | `/api/v1/tasks/statistics` | Get aggregated task counts and overdue metrics |
| `GET` | `/api/v1/tasks/{task_id}` | Retrieve single task (returns 404 if not owned by user) |
| `PATCH` | `/api/v1/tasks/{task_id}` | Partial update (updates `completed_at` automatically) |
| `DELETE` | `/api/v1/tasks/{task_id}` | Delete task |
| `POST` | `/api/v1/tasks/{task_id}/duplicate` | Duplicate task with reset status and new UUID |
| `PATCH` | `/api/v1/tasks/{task_id}/archive` | Move task to archived state |
| `PATCH` | `/api/v1/tasks/{task_id}/restore` | Restore archived task to active state |

### Query Parameters for `GET /api/v1/tasks`:
- `page`: Page number (default `1`, min `1`).
- `page_size`: Items per page (default `20`, max `100`).
- `search`: Search string matched case-insensitively in title or description.
- `status`: Filter by `TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
- `priority`: Filter by `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
- `due_date_from` / `due_date_to`: ISO 8601 date range filters.
- `is_archived`: Boolean flag (default `false`).
- `sort_by`: `created_at`, `updated_at`, `due_date`, `priority`, `status`, `title`.
- `sort_order`: `desc` (default) or `asc`.

---

## 4. Multi-User Security & Isolation Rules

1. **Identity Resolution**: `user_id` is extracted strictly from the JWT access token subject via the FastAPI dependency `get_current_user`.
2. **Zero Client Trust**: Endpoints never accept `user_id` in request payloads.
3. **Strict Query Scoping**: Every SQL query across `TaskRepository` filters strictly by `Task.user_id == user_id`.
4. **Uniform 404 Responses**: If a user attempts to view, update, delete, duplicate, archive, or restore a task belonging to another user, the API responds with `404 Not Found` (`"Task not found."`), giving attackers zero information regarding whether the resource exists.

---

## 5. Dynamic Overdue Definition

A task is dynamically flagged as `is_overdue = True` if:
- It is not `COMPLETED` and not `CANCELLED`.
- `due_date` is present and earlier than the current UTC timestamp.
Completed or cancelled tasks are never marked overdue.

