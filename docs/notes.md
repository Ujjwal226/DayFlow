# DayFlow — Stage 3D: Notes & Knowledge Management Documentation

## 1. Overview & Architecture

The **Notes & Knowledge Management** module provides DayFlow users with a Markdown-powered personal knowledge repository. Notes are first-class entities with dedicated database persistence, flexible multi-tagging, optional categorization, and relational links to DayFlow projects and tasks.

```
┌────────────────────────────────────────────────────────┐
│                       NotesPage                        │
│   (Search, Category Filter, Tag Filter, Active/Archive)│
└───────────────┬────────────────────────┬───────────────┘
                │                        │
┌───────────────▼────────┐      ┌────────▼───────────────┐
│       NoteSidebar      │      │       NoteEditor       │
│  - New note action     │      │ - Debounced Autosave   │
│  - Search input        │      │ - Markdown Formatting  │
│  - Active/Archive tabs │      │ - Real-time Preview    │
│  - Category/Tag lists  │      │ - Split View           │
├────────────────────────┤      └────────┬───────────────┘
│        NoteCard        │               │
│  - Pinned notes        │      ┌────────▼───────────────┐
│  - Regular notes       │      │   NoteMetadataPanel    │
│  - Pin / Archive / Del │      │ - Category Assignment  │
└────────────────────────┘      │ - Project Association  │
                                │ - Task Association     │
                                │ - Multi-Tag Selector   │
                                └────────┬───────────────┘
                                         │
┌────────────────────────────────────────▼───────────────┐
│            DayFlow Notes Backend REST API              │
│                 /api/v1/notes (CRUD)                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Database Models & Alembic Migration

### Migration Revision: `9f12a3b4c5d6`
- **Revises**: `8a45d07e12f3` (Stage 3B Calendar Events)
- **Heads**: Single head confirmed (`9f12a3b4c5d6`).

### Tables Created:
1. `notes`:
   - `id`: UUID (Primary Key).
   - `user_id`: UUID (Foreign Key `users.id` with `CASCADE` delete).
   - `title`: String(255) (Non-empty).
   - `content`: Text (Markdown content, defaults to empty string).
   - `is_pinned`: Boolean (Default false, indexed).
   - `is_archived`: Boolean (Default false, indexed).
   - `category_id`: UUID (Foreign Key `categories.id` with `SET NULL` on delete).
   - `project_id`: UUID (Foreign Key `projects.id` with `SET NULL` on delete).
   - `task_id`: UUID (Foreign Key `tasks.id` with `SET NULL` on delete).
   - `created_at` / `updated_at`: DateTime(timezone=True) with indices.
   - Composite indices on `(user_id, is_archived)`, `(user_id, is_pinned)`, `(user_id, updated_at)`, `(user_id, project_id)`, and `(user_id, task_id)` for multi-tenant query performance.
2. `note_tags`:
   - `note_id`: UUID (Foreign Key `notes.id` with `CASCADE`).
   - `tag_id`: UUID (Foreign Key `tags.id` with `CASCADE`).
   - `created_at`: DateTime(timezone=True).
   - Primary key on `(note_id, tag_id)` and secondary index on `(tag_id, note_id)`.

---

## 3. Backend API Endpoints

All endpoints are strictly authenticated and tenant-isolated under prefix `/api/v1/notes`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/notes` | List paginated notes with filters (`search`, `is_pinned`, `is_archived`, `category_id`, `project_id`, `task_id`, `tag_id`). |
| `POST` | `/api/v1/notes` | Create a new note with optional associations and tag list. |
| `GET` | `/api/v1/notes/{id}` | Retrieve a single note with eagerly loaded associations. |
| `PATCH` | `/api/v1/notes/{id}` | Update title, content, pin/archive flags, or detach/attach associations. |
| `DELETE` | `/api/v1/notes/{id}` | Permanently delete a note. |

---

## 4. Markdown Editor & Security

- **Editor Capabilities**:
  - Headings (`#`, `##`, `###`).
  - Bold (`**text**`) and Italic (`*text*`).
  - Bulleted lists (`- `) and numbered lists (`1. `).
  - Interactive checklists (`- [ ] ` and `- [x] `).
  - Blockquotes (`> `).
  - Code blocks (```` ``` ````) and inline code (`` `code` ``).
  - Formatted links (`[title](url)`).
- **Editor Modes**:
  - **Edit**: Focused raw Markdown input.
  - **Preview**: Rendered visual layout.
  - **Split**: Simultaneous writing and real-time rendered preview.
- **XSS Prevention & Security**:
  - Safe link validation enforces `http://`, `https://`, and `mailto:` schemes, rejecting `javascript:` or `data:` URIs.
  - Uses native React tokenization without `dangerouslySetInnerHTML`.

---

## 5. Saving Behavior

- **Autosave**: Debounced at 1000ms after user typing ceases.
- **Save Status Feedback**: Visual status indicator displaying `Saving...` (animated), `Saved` (with timestamp), `Unsaved edits`, or `Save failed`.
- **Explicit Save**: Immediate "Save Now" button for instant persistence.
- **Navigation Protection**: Switching active notes automatically flushes pending unsaved changes before switching.

---

## 6. Testing Commands

### Backend Tests
```bash
# Targeted notes tests
python -m pytest backend/tests/test_notes.py -o pythonpath=backend -v

# Full regression test suite
python -m pytest backend/tests/ -o pythonpath=backend
```

### Frontend Tests
```bash
# Targeted notes tests
npx vitest run note

# Full frontend test suite
npm test -- --run

# ESLint & Build
npm run lint
npm run build
```

