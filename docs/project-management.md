# DayFlow — Project Management Module (Implementation 2C)

## 1. Overview

The Project Management module provides multi-user project organization within DayFlow. Authenticated users can group existing top-level tasks into projects, track deadlines, monitor dynamic project completion percentages, and filter project-specific tasks.

---

## 2. Data Model & Relationships

### `projects` Table
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to `users.id`, `ON DELETE CASCADE`, indexed)
- `name` (VARCHAR(150), required, trimmed)
- `description` (TEXT, optional)
- `status` (`project_status` Enum: `PLANNED`, `ACTIVE`, `ON_HOLD`, `COMPLETED`, default: `PLANNED`)
- `priority` (`project_priority` Enum: `LOW`, `MEDIUM`, `HIGH`, `URGENT`, default: `MEDIUM`)
- `start_date` (DATE, optional)
- `due_date` (DATE, optional, indexed)
- `color` (VARCHAR(7), optional hex color code, default: `#3B82F6`)
- `is_archived` (BOOLEAN, default `false`, indexed)
- `created_at` (TIMESTAMP WITH TIME ZONE, default: `now()`)
- `updated_at` (TIMESTAMP WITH TIME ZONE, default: `now()`)

### `tasks` Table Extension
- `project_id` (UUID, nullable, Foreign Key to `projects.id`, `ON DELETE SET NULL`, indexed)
  - Tasks belong to at most one project.
  - Deleting a project preserves all tasks and unlinks them (`project_id = NULL`).
  - Subtasks (`parent_task_id IS NOT NULL`) cannot be assigned directly to projects and are excluded from project task lists and project statistics.

---

## 3. Dynamic Progress & Statistics

Project statistics are calculated dynamically via SQL aggregation without storing stale percentages:

$$\text{Completion Percentage} = \frac{\text{Completed Tasks}}{\text{Total Tasks}} \times 100$$

* If `Total Tasks == 0`, `Completion Percentage = 0.0%`.
* Subtasks are excluded (`parent_task_id IS NULL`).
* Archived tasks are excluded from active statistics (`is_archived = false`).
* Marking all tasks completed does not automatically change the project status to `COMPLETED`; project status is user-controlled.

---

## 4. REST API Endpoints

### Projects
* `POST /api/v1/projects` — Create project for current user.
* `GET /api/v1/projects` — List paginated projects with search, status, priority, and archive filters.
* `GET /api/v1/projects/{project_id}` — Get single project with dynamic statistics.
* `PATCH /api/v1/projects/{project_id}` — Partial update with date order validation.
* `DELETE /api/v1/projects/{project_id}` — Delete project (sets `tasks.project_id = NULL`).
* `PATCH /api/v1/projects/{project_id}/archive` — Archive project.
* `PATCH /api/v1/projects/{project_id}/restore` — Restore archived project.
* `GET /api/v1/projects/{project_id}/statistics` — Dynamic task statistics.
* `GET /api/v1/projects/{project_id}/tasks` — Paginated list of tasks in project.

### Task Assignment
* `PUT /api/v1/projects/{project_id}/tasks/{task_id}` — Assign task to project.
* `DELETE /api/v1/projects/{project_id}/tasks/{task_id}` — Remove task from project.

---

## 5. Security & Multi-User Isolation

1. **Session-Derived Ownership:** `user_id` is derived strictly from the JWT bearer token via `get_current_user`.
2. **Strict Scoping:** All project queries filter by `user_id == current_user.id`.
3. **Cross-Tenant Prevention:**
   - Attempting to view, update, delete, or list tasks for another user's project returns HTTP 404.
   - Attempting to assign another user's task to a project or assign a task to another user's project returns HTTP 404.
   - Creating a task with a foreign `project_id` returns HTTP 404.

---

## 6. Migration Details

* Migration ID: `7e8866728b79`
* Down revision: `84790214dd00`
* Tested reversible via:
  ```bash
  alembic downgrade -1
  alembic upgrade head
  alembic check
  ```

---

## 7. Testing Instructions

### Backend
```bash
$env:PYTHONPATH="C:\Projects\DayFlow\backend"
python -m pytest backend/tests/test_projects.py -v
python -m pytest -v
```

### Frontend
```bash
cd frontend
npm test -- --run
npm run build
npm run lint
```

