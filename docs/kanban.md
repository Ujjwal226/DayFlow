# DayFlow — Stage 3C: Kanban Board Module Documentation

## 1. Overview & Architecture

DayFlow's Kanban Board provides a visual, responsive workflow for managing personal and project tasks across their lifecycle. Rather than duplicating task state in a custom database entity or storing state locally in the browser, the Kanban module operates as a visual workflow projection directly on top of the existing DayFlow `Task` entity and standard REST API (`/api/v1/tasks`).

```
┌────────────────────────────────────────────────────────┐
│                      KanbanPage                        │
│   (Search, Project Filter, Category Filter, Priority)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                      KanbanBoard                       │
│        (Horizontal 4-Column Responsive Grid)           │
├─────────────┬──────────────┬──────────────┬────────────┤
│   TODO      │ IN_PROGRESS  │  COMPLETED   │ CANCELLED  │
│ (Drop zone) │ (Drop zone)  │ (Drop zone)  │(Drop zone) │
└─────────────┴──────────────┴──────────────┴────────────┘
                            │
              Native HTML5 Drag & Drop /
              Accessible Status Selector
                            │
       Optimistic UI Update + Auto-Rollback on Error
                            │
┌───────────────────────────▼────────────────────────────┐
│           Existing DayFlow Tasks Backend API           │
│        PATCH /api/v1/tasks/{id} {"status": "..."}      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Status Columns

The Kanban board maps directly to DayFlow's `TaskStatus` enumeration values:

1. **`TODO`** (To Do): Unstarted tasks.
2. **`IN_PROGRESS`** (In Progress): Active tasks currently being worked on.
3. **`COMPLETED`** (Completed): Finished tasks with visual completion styling.
4. **`CANCELLED`** (Cancelled): Tasks cancelled or no longer needed.

Each column features:
- Colored status indicator dot and title.
- Dynamic count pill reflecting the current number of tasks.
- Quick `+` button in the column header to create a new task directly with that status preselected.
- Interactive drag-over drop target with active emerald borders and background highlight.
- Empty state with guidance when no tasks match the column.

---

## 3. Drag-and-Drop Implementation & Dependency Choice

- **Approach**: Built using the native HTML5 Drag and Drop API (`draggable={true}`, `onDragStart`, `onDragEnd`, `onDragOver`, `onDragLeave`, `onDrop`).
- **Rationale**: 
  - Zero third-party runtime dependencies required.
  - Native browser performance without bundle bloat.
  - Full TypeScript and Tailwind CSS styling compatibility.
- **Optimistic Updates & Error Rollback**:
  - When a task card is dropped onto a target column, DayFlow immediately updates the React state to move the card to the new column.
  - A background `PATCH /api/v1/tasks/{id}` request is dispatched with `{ status: targetStatus }`.
  - While the update is in flight, the card is visually dimmed and interactive re-dragging is locked to prevent race conditions.
  - If the API call fails or the network errors out, the task is automatically restored to its original column and an error alert is presented to the user with a dismiss action.

---

## 4. Accessibility & Responsive Design

- **Accessible Status Changer**: In addition to drag-and-drop, every task card includes a semantic keyboard-navigable `<select aria-label="Change status for ...">` element allowing keyboard-only users, screen readers, and touch-screen devices to move tasks between columns without mouse dragging.
- **Task Cards**: Accessible focus outlines, ARIA labels, semantic buttons for edit and delete actions with confirmation dialogs.
- **Desktop Layout**: Horizontal 4-column layout (`min-w-[280px]` per column with horizontal scrolling container if viewport narrows).
- **Mobile Layout**: Horizontally scrollable flex track with full snap-scroll support on smartphones and tablets.

---

## 5. Filters & Search

- **Real-Time Search**: Filter tasks by title and description substring.
- **Project Filter**: Filter by "All Projects", "No Project", or individual projects owned by the user.
- **Category Filter**: Filter by category.
- **Priority Filter**: Filter by `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
- **Recurring Filter**: Show only tasks originating from recurring task series.
- **Clear Filters**: One-click reset when active filters are engaged.
- **Task Counter**: Live indicator displaying matched tasks vs. total tasks.

---

## 6. Integration Points

- **Task Creation & Editing**: Fully integrates the standard `TaskFormModal` from `components/tasks/TaskForm`, prefilling column status on creation and refreshing the board upon submit.
- **Top Navigation**: Navigation links integrated into `DashboardPage`, `CalendarPage`, and `TasksPage`.
- **Route**: Protected route registered at `/kanban` in `routes/index.tsx`.

