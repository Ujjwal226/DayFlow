# DayFlow — Categories, Tags & Subtasks Architecture

## 1. Overview

Implementation 2B introduces three core capabilities to DayFlow's productivity engine:
1. **Custom Categories**: Single-user ownership, unique normalized naming, color/icon tags, and safe uncategorization upon deletion.
2. **Reusable Tags**: Many-to-many associations with tasks via an explicit `task_tags` table, user isolation, and preserved tasks on tag deletion.
3. **Subtasks & Parent Progress**: Self-referential single-nesting tasks (`parent_task_id`), cascading deletion, dynamic calculation of progress percentages, and exclusion of subtasks from top-level list queries.

---

## 2. Database Models & Schema

### `categories` Table
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> `users.id`, `ON DELETE CASCADE`, indexed)
- `name`: VARCHAR(100), required
- `name_normalized`: VARCHAR(100), lowercased unique constraint with `user_id` (`uq_categories_user_id_name_normalized`)
- `description`: TEXT, optional
- `color`: VARCHAR(7), hexadecimal color format (`#RRGGBB`)
- `icon`: VARCHAR(50), optional
- `created_at`, `updated_at`: TIMESTAMPTZ

### `tags` Table
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> `users.id`, `ON DELETE CASCADE`, indexed)
- `name`: VARCHAR(50), required
- `name_normalized`: VARCHAR(50), lowercased unique constraint with `user_id` (`uq_tags_user_id_name_normalized`)
- `color`: VARCHAR(7), optional hex color
- `created_at`, `updated_at`: TIMESTAMPTZ

### `task_tags` Table (Association)
- `task_id`: UUID (Foreign Key -> `tasks.id`, `ON DELETE CASCADE`, Composite PK)
- `tag_id`: UUID (Foreign Key -> `tags.id`, `ON DELETE CASCADE`, Composite PK)
- `created_at`: TIMESTAMPTZ
- Indexes on `(tag_id, task_id)` and `tag_id`

### Extended `tasks` Table
- `category_id`: UUID (Foreign Key -> `categories.id`, `ON DELETE SET NULL`, indexed with `user_id`)
- `parent_task_id`: UUID (Foreign Key -> `tasks.id`, `ON DELETE CASCADE`, indexed with `user_id`)

---

## 3. Subtask Progress Calculation

Parent tasks derive progress dynamically on read operations:
- `total_subtasks`: Total count of child tasks where `parent_task_id == parent.id`
- `completed_subtasks`: Count of child tasks where `status == TaskStatus.COMPLETED`
- `remaining_subtasks`: `total_subtasks - completed_subtasks`
- `progress_percentage`: `round((completed_subtasks / total_subtasks) * 100.0, 1)` (or `0.0` if no subtasks exist)

Parent status remains independent: completion of all subtasks does not automatically mark a parent task as completed.

---

## 4. API Endpoints

### Categories
- `POST /api/v1/categories` — Create category
- `GET /api/v1/categories` — List user categories with task counts
- `GET /api/v1/categories/{category_id}` — Get category
- `PATCH /api/v1/categories/{category_id}` — Update category
- `DELETE /api/v1/categories/{category_id}` — Delete category (sets `tasks.category_id = NULL`)
- `GET /api/v1/categories/{category_id}/tasks` — List tasks under category

### Tags
- `POST /api/v1/tags` — Create tag
- `GET /api/v1/tags` — List user tags with task counts
- `GET /api/v1/tags/{tag_id}` — Get tag
- `PATCH /api/v1/tags/{tag_id}` — Update tag
- `DELETE /api/v1/tags/{tag_id}` — Delete tag (removes associations from `task_tags`)

### Task Category & Tag Assignment
- `PATCH /api/v1/tasks/{task_id}/category` — Set or clear task category
- `PUT /api/v1/tasks/{task_id}/tags` — Replace assigned tags for task

### Subtasks
- `POST /api/v1/tasks/{task_id}/subtasks` — Create subtask under parent
- `GET /api/v1/tasks/{task_id}/subtasks` — List parent's subtasks
- `GET /api/v1/subtasks/{subtask_id}` — Get subtask
- `PATCH /api/v1/subtasks/{subtask_id}` — Update subtask
- `DELETE /api/v1/subtasks/{subtask_id}` — Delete subtask

---

## 5. Security & Multi-User Isolation

- All queries filter strictly by `user_id == current_user.id`.
- Foreign resources return uniform `404 Not Found` responses to prevent ID enumeration.
- Category assignment validates that the category belongs to the current user.
- Tag assignment validates that all tag IDs belong to the current user.
- Subtask creation verifies that the parent task belongs to the current user.
- Single nesting limit: Attempts to create a subtask under a task that already has a `parent_task_id` are rejected with HTTP 422.

---

## 6. Migration Guide

The migration `84790214dd00_create_categories_tags_and_subtasks.py` applies all schema changes while preserving existing task rows:
```bash
cd backend
.venv\Scripts\alembic upgrade head
```
To revert:
```bash
.venv\Scripts\alembic downgrade -1
```

