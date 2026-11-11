# DayFlow Stage 3G: Strategic Goals & Planning Module

## 1. Overview & Architecture

The **Goals & Planning Module** implements an end-to-end goal tracking and alignment workspace for DayFlow. It bridges long-term aspirations with daily tactical execution by allowing users to establish high-level strategic goals, decompose them into milestones, link individual daily tasks, and schedule daily, weekly, and monthly planning commitments.

### Core Objectives
1. **Multi-Horizon Strategic Management**: Support high-level outcome goals, numeric measurable targets (e.g. running km, book pages read), and milestone-driven achievements.
2. **Deterministic Progress Strategies**: Progress can be computed manually, automatically via milestone completion ratio, or proportionally based on measurable numeric metrics.
3. **Task & Project Alignment**: Direct foreign key and link associations connecting existing DayFlow projects and individual tasks to overarching strategic goals.
4. **Planning Periods**: Daily, Weekly, and Monthly planning commitments enabling tactical breakdown and tracking of immediate action items.
5. **Security & Data Isolation**: Strict user-level authorization preventing cross-user associations, linking of foreign tasks or projects, and unauthenticated access.
6. **Notification Integration**: Leverages the Stage 3E in-app notification system to alert users when a strategic goal reaches 100% completion.

---

## 2. Database Schema & Data Models

The module is powered by five normalized PostgreSQL tables defined in [`backend/app/models/goal.py`](file:///C:/Projects/DayFlow/backend/app/models/goal.py) and migrated via Alembic revision `d4e5f6a7b8c9` (`create_goals_tables.py`).

### 2.1 Entity Relationship Diagram

```
       +-----------------------+
       |         User          |
       +-----------------------+
                   |
         +---------+---------+
         | 1                 | 1
         |                   |
         v *                 v *
+-----------------+   +--------------------+
|      Goal       |   | PlanningObjective  |
+-----------------+   +--------------------+
| id (UUID PK)    |   | id (UUID PK)       |
| user_id (FK)    |   | user_id (FK)       |
| project_id (FK) |   | goal_id (FK Null)  |
| title           |   | task_id (FK Null)  |
| category        |   | period_type        |
| goal_type       |   | period_date        |
| priority        |   | title              |
| status          |   | is_completed       |
| progress_method |   +--------------------+
| progress_pct    |
| target_value    |
| current_value   |
| unit            |
+-----------------+
    |         |
    | 1       | 1
    v *       v *
+-----------+ +------------------+
| Milestone | |   GoalTaskLink   |
+-----------+ +------------------+
| id (PK)   | | goal_id (PK, FK) |
| goal_id   | | task_id (PK, FK) |
| title     | +------------------+
| due_date  |
| completed |
| order_idx |
+-----------+
```

### 2.2 Table Definitions

1. `goals`
   - `id`: UUID (Primary Key)
   - `user_id`: UUID (Foreign Key to `users.id`, `ON DELETE CASCADE`)
   - `project_id`: UUID (Foreign Key to `projects.id`, `ON DELETE SET NULL`)
   - `title`: String(200), indexed, non-nullable
   - `description`: Text, nullable
   - `category`: Enum (`PERSONAL`, `CAREER`, `LEARNING`, `HEALTH`, `FINANCE`, `PROJECTS`, `OTHER`)
   - `goal_type`: Enum (`OUTCOME`, `NUMERIC`, `MILESTONE`)
   - `priority`: Enum (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
   - `status`: Enum (`NOT_STARTED`, `IN_PROGRESS`, `ON_TRACK`, `AT_RISK`, `COMPLETED`, `CANCELLED`)
   - `progress_method`: Enum (`MANUAL`, `MILESTONE`, `NUMERIC`)
   - `progress_percentage`: Float (0.0 to 100.0)
   - `target_value`: Float, nullable
   - `current_value`: Float, nullable
   - `unit`: String(50), nullable
   - `start_date`: Date, nullable
   - `target_date`: Date, nullable
   - `completed_at`: DateTime(timezone=True), nullable
   - `is_archived`: Boolean (default False)

2. `goal_milestones`
   - Sequential milestones representing checkpoints toward goal attainment.
   - Cascades deletion when parent goal is removed. Includes `order_index` for user-defined reordering.

3. `goal_task_links`
   - Join table providing an explicit link between a `Goal` and a `Task`.
   - Unique constraint `(goal_id, task_id)`.

4. `planning_objectives`
   - Scheduled commitments associated with a `DAILY`, `WEEKLY`, or `MONTHLY` period date.
   - May link to a specific goal or stand independently as a planning period commitment.

5. `goal_activities`
   - Audit trail capturing mutations (`CREATED`, `UPDATED`, `COMPLETED`, `REOPENED`, `MILESTONE_COMPLETED`, `TASK_LINKED`).

---

## 3. Progress Calculation & Lifecycle Semantics

Goal progress calculation behavior depends on the configured `progress_method`:

| Strategy | Formula | Automation Rules |
|---|---|---|
| `MANUAL` | Explicitly user-set percentage ($0 - 100\%$). | Never overwritten by milestone or metric updates. Reopening resets progress to 90% if previously 100%. |
| `MILESTONE` | $\frac{\text{Completed Milestones}}{\text{Total Milestones}} \times 100$ | Automatically recalculated whenever a milestone is added, deleted, completed, or uncompleted. Reaching 100% transitions goal status to `COMPLETED`. |
| `NUMERIC` | $\min\left(100, \frac{\text{Current Value}}{\text{Target Value}} \times 100\right)$ | Automatically updated when current or target values change. Reaching 100% automatically sets status to `COMPLETED`. |

### Completion & In-App Notifications
When a goal transitions to `COMPLETED` (either explicitly or via automated progress recalculation):
- `completed_at` timestamp is stamped with UTC `datetime.now(timezone.utc)`.
- An in-app notification of type `SYSTEM_ALERT` is dispatched via Stage 3E's notification engine:
  - Title: `"Goal Completed: {goal.title}"`
  - Body: `"Congratulations! You have completed your goal '{goal.title}'."`

---

## 4. API Endpoints

All routes are mounted under `/api/v1/goals`:

### Goal Management
- `POST /api/v1/goals`: Create a new strategic goal.
- `GET /api/v1/goals`: List goals with filters (`category`, `status`, `priority`, `project_id`, `search`, `page`, `page_size`).
- `GET /api/v1/goals/{id}`: Retrieve detailed goal with milestones and linked tasks.
- `PATCH /api/v1/goals/{id}`: Update goal attributes or manual progress.
- `DELETE /api/v1/goals/{id}`: Delete goal and its milestones.
- `POST /api/v1/goals/{id}/complete`: Explicitly complete goal and stamp completion time.
- `POST /api/v1/goals/{id}/reopen`: Reopen completed goal to `IN_PROGRESS`.
- `GET /api/v1/goals/{id}/activities`: View audit trail of lifecycle events.
- `GET /api/v1/goals/analytics`: Aggregate KPI metrics (total, active, completed, at-risk, completion rate, breakdown by category/status/priority).

### Milestone Management
- `POST /api/v1/goals/{id}/milestones`: Add a milestone.
- `PATCH /api/v1/goals/milestones/{milestone_id}`: Toggle completion status or update title.
- `DELETE /api/v1/goals/milestones/{milestone_id}`: Remove a milestone.
- `POST /api/v1/goals/{id}/milestones/reorder`: Persist custom ordering sequence.

### Task Linking
- `POST /api/v1/goals/{id}/tasks`: Link a task to the goal (validates ownership of both).
- `DELETE /api/v1/goals/{id}/tasks/{task_id}`: Unlink task.

### Planning Periods
- `POST /api/v1/goals/planning/objectives`: Create daily/weekly/monthly objective.
- `GET /api/v1/goals/planning/summary`: Fetch period summary with completion metrics and objectives.
- `PATCH /api/v1/goals/planning/objectives/{id}`: Toggle objective completion.
- `DELETE /api/v1/goals/planning/objectives/{id}`: Delete objective.

---

## 5. Frontend Architecture & Views

The frontend interface is implemented at [`frontend/src/pages/GoalsPage.tsx`](file:///C:/Projects/DayFlow/frontend/src/pages/GoalsPage.tsx) accessible via the `/goals` route and top navigation bar.

### Components
1. **GoalCard (`GoalCard.tsx`)**:
   - Visual badges for status, priority, and category.
   - Dynamic progress bar with color thresholds (amber $\rightarrow$ indigo $\rightarrow$ emerald $\rightarrow$ teal).
   - Quick action controls for completion toggle, editing, and deletion.
2. **GoalDetailModal (`GoalDetailModal.tsx`)**:
   - Tabbed view:
     - **Milestones**: Add, check off, delete, and reorder checkpoints with visual feedback.
     - **Linked Tasks**: Link existing user tasks, view status, and unlink.
     - **Activity**: Overview of lifecycle auditing.
3. **GoalFormModal (`GoalFormModal.tsx`)**:
   - Clean dialog supporting both create and edit flows.
   - Progress strategy selector dynamically switching between Manual Slider, Milestone preview, and Numeric Target inputs.
   - Project association dropdown populated from existing user projects.
4. **PlanningBoard (`PlanningBoard.tsx`)**:
   - Daily, Weekly, and Monthly tabs with bidirectional date navigation.
   - Progress bar tracking commitment completion rate.
   - Inline creation form allowing quick scheduling of commitments linked to strategic goals.
5. **GoalAnalyticsCard (`GoalAnalyticsCard.tsx`)**:
   - Summary metric cards displaying Active Goals, Completed Goals, Average Progress %, and At-Risk count.
   - Categorical breakdown tags.

---

## 6. Verification & Test Coverage

### Test Suites
- **Backend Tests (`backend/tests/test_goals.py`)**:
  - `test_goal_crud_lifecycle_and_ownership`: Tests creation, update, deletion, activity audit, and cross-user isolation.
  - `test_milestone_management_and_progress_calculation`: Validates milestone addition, 50% and 100% automated recalculation, and reordering.
  - `test_numeric_measurable_goal_progress`: Validates proportional progress calculation and auto-completion when target is met.
  - `test_task_and_project_linking_and_cross_user_security`: Validates linking, unlinking, and strict 404 security rejection when linking other users' tasks or projects.
  - `test_planning_objectives_daily_weekly_monthly`: Tests daily/weekly/monthly periods, completion toggles, and summaries.
  - `test_goal_analytics_aggregation`: Validates KPI calculations, category grouping, and priority distributions.
  - **Full Backend Suite**: 174 passed, 0 failures.

- **Frontend Tests (`frontend/src/test/goalsPage.test.tsx`)**:
  - Comprehensive Vitest + React Testing Library coverage for GoalsPage, GoalCard, Milestone toggling, and creation modal.
  - **Full Frontend Suite**: 116 passed across 31 test files.
  - **Build Verification**: `tsc -b` and `vite build` completed with 0 errors.
