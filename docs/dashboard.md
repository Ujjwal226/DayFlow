# DayFlow Dashboard & Personal Workspace Architecture

Stage 3A introduces DayFlow's modular, responsive, customizable dashboard and personal workspace.

## 1. Overview & Architecture

The DayFlow dashboard allows authenticated users to customize and persist their personal workspace layout. The architecture decouples layout persistence from widget presentation and data fetching:

```
┌─────────────────────────────────────────────────────────────┐
│                       DashboardPage                         │
│  - Fetches user layout from Backend                         │
│  - Renders DashboardGrid with responsive CSS Grid           │
│  - Manages DashboardCustomizerModal                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌─────────────────────────┐   ┌──────────────────────────┐
   │      DashboardGrid      │   │ DashboardCustomizerModal │
   │  - Filters visible      │   │  - Visibility toggles    │
   │  - Sorts by order       │   │  - Reorder up/down       │
   │  - Error boundary wrap  │   │  - Size selectors        │
   │  - Renders 10 widgets   │   │  - Save / Reset / Cancel │
   └────────────┬────────────┘   └─────────────┬────────────┘
                │                              │
                ▼                              ▼
   ┌─────────────────────────┐   ┌──────────────────────────┐
   │     Widget Registry     │   │      Dashboard API       │
   │ (components/dashboard/  │   │   (api/dashboard.ts)     │
   │      registry.ts)       │   │  - GET /layout           │
   │  - 10 widget definitions│   │  - PUT /layout           │
   │  - Safe fallback        │   │  - POST /layout/reset    │
   └─────────────────────────┘   └──────────────────────────┘
```

## 2. Supported Dashboard Widgets

The dashboard registers 10 core widgets:

| ID | Title | Default Size | Default Visible | Source Service | Description |
|---|---|---|---|---|---|
| `welcome` | Welcome & Profile | `full` | `true` | `useAuth()` | Authenticated profile, verification status, and resend warnings. |
| `productivity_overview` | Productivity Overview | `full` | `true` | `analyticsApi` | Trailing 30-day KPIs: completion rate, net completions, active tasks. |
| `today_tasks` | Today's Tasks | `medium` | `true` | `tasksApi` | Top-level tasks due today with priority and status badges. |
| `upcoming_tasks` | Upcoming Tasks | `medium` | `true` | `tasksApi` | Tasks scheduled across the forward 7-day window. |
| `overdue_tasks` | Overdue Tasks | `medium` | `true` | `tasksApi` | Incomplete tasks past their due date requiring immediate attention. |
| `recent_activity` | Recent Activity | `medium` | `true` | `activityLogsApi` | Chronological activity feed showing the latest 5 actions. |
| `projects_overview` | Projects Overview | `medium` | `true` | `projectsApi` | Active non-archived projects with progress bars and task counts. |
| `productivity_trends` | Productivity Trends | `medium` | `true` | `analyticsApi` | Trailing 7-day daily velocity and net completion bars. |
| `recurring_insights` | Recurring Tasks | `medium` | `true` | `recurringTasksApi` | Active recurring rules, frequencies, and next occurrence dates. |
| `quick_actions` | Quick Actions | `full` | `true` | Internal links | Direct shortcuts to create tasks, projects, recurring series, or view analytics. |

## 3. Dashboard Layout Persistence API

Layout configurations are stored per user in the backend PostgreSQL/SQLite database via the `dashboard_layouts` table.

### Endpoints

- `GET /api/v1/dashboard/layout`:
  - Returns the user's saved layout configuration if present.
  - If no customized layout exists, returns the centralized default layout (`is_customized: false`, `id: null`) **without writing any rows to the database**.
- `PUT /api/v1/dashboard/layout`:
  - Persists full replacement of the user's widget configurations (`widgets: [{ widget_id, is_visible, order, size }]`).
  - Validates that all 10 registered widget IDs are present with unique, non-negative orders.
- `POST /api/v1/dashboard/layout/reset`:
  - Deletes any saved customized layout row for the authenticated user and returns the default layout.

## 4. Widget Visibility, Sizing & Ordering

- **Visibility**: Hidden widgets are completely unmounted by `DashboardGrid`. They do not issue background network requests or cause unnecessary re-renders.
- **Sizing**:
  - `small`: 1 column on desktop (`col-span-12 md:col-span-6 lg:col-span-4`).
  - `medium`: 2 columns on desktop (`col-span-12 md:col-span-6 lg:col-span-6`).
  - `full`: Spans entire row (`col-span-12`).
  - On mobile viewports (<768px), all widgets cleanly adapt to single-column width (`col-span-12`).
- **Ordering**: Widgets are rendered in ascending order of their `order` index. Ordering is customized via accessible Move Up and Move Down controls in `DashboardCustomizerModal`.

## 5. Failure Isolation & Error Boundaries

- **API Failure Isolation**: Each widget independently manages loading and error states via `WidgetContainer`. A failed API request in one widget displays a localized retry card without affecting other widgets.
- **React Render Error Isolation**: Every widget in `DashboardGrid` is wrapped in `WidgetErrorBoundary`. Any unhandled JavaScript runtime error during widget rendering is caught locally, displaying an error fallback card while sibling widgets continue functioning.

## 6. Registering Future Widgets

Future modules (such as Notes, Goals, Focus, or Finance) can be integrated into the dashboard by:

1. Adding the new identifier to `DashboardWidgetId` in `backend/app/core/dashboard_registry.py` and `frontend/src/types/dashboard.ts`.
2. Defining default metadata in `WIDGET_METADATA` in `backend/app/core/dashboard_registry.py`.
3. Creating the widget component in `frontend/src/components/dashboard/widgets/`.
4. Registering the component in `frontend/src/components/dashboard/registry.ts`.

