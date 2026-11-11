import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { GoalsPage } from '../pages/GoalsPage';
import { goalsApi } from '../api/goals';
import { tasksApi } from '../api/tasks';
import { projectsApi } from '../api/projects';
import { Goal, GoalAnalyticsOverview, PlanningPeriodSummary } from '../types/goal';

vi.mock('../api/goals');
vi.mock('../api/tasks');
vi.mock('../api/projects');

const mockGoals: Goal[] = [
  {
    id: 'goal-1',
    user_id: 'user-1',
    title: 'Learn Distributed Systems',
    description: 'Read papers and implement raft',
    category: 'LEARNING',
    goal_type: 'OUTCOME',
    priority: 'HIGH',
    status: 'IN_PROGRESS',
    progress_method: 'MILESTONE',
    progress_percentage: 50,
    target_value: null,
    current_value: null,
    unit: null,
    start_date: '2026-01-01',
    target_date: '2026-12-31',
    completed_at: null,
    project_id: null,
    is_archived: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    milestones: [
      {
        id: 'ms-1',
        goal_id: 'goal-1',
        user_id: 'user-1',
        title: 'Read Raft paper',
        description: null,
        due_date: null,
        is_completed: true,
        order_index: 0,
        completed_at: '2026-02-01T00:00:00Z',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
      {
        id: 'ms-2',
        goal_id: 'goal-1',
        user_id: 'user-1',
        title: 'Implement Raft consensus in Go',
        description: null,
        due_date: null,
        is_completed: false,
        order_index: 1,
        completed_at: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ],
    linked_tasks: [],
    milestone_count: 2,
    completed_milestone_count: 1,
    linked_task_count: 0,
    completed_task_count: 0,
  },
  {
    id: 'goal-2',
    user_id: 'user-1',
    title: 'Run Marathon 2026',
    description: 'Weekly running goal',
    category: 'HEALTH',
    goal_type: 'NUMERIC',
    priority: 'MEDIUM',
    status: 'COMPLETED',
    progress_method: 'NUMERIC',
    target_value: 42,
    current_value: 42,
    unit: 'km',
    progress_percentage: 100,
    start_date: '2026-01-01',
    target_date: '2026-10-10',
    completed_at: '2026-10-10T12:00:00Z',
    project_id: null,
    is_archived: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-10-10T12:00:00Z',
    milestones: [],
    linked_tasks: [],
    milestone_count: 0,
    completed_milestone_count: 0,
    linked_task_count: 0,
    completed_task_count: 0,
  },
];

const mockAnalytics: GoalAnalyticsOverview = {
  total_goals: 2,
  active_goals: 1,
  completed_goals: 1,
  at_risk_goals: 0,
  completion_rate: 50,
  average_progress_percentage: 75,
  milestone_completion_rate: 50,
  linked_task_completion_rate: 0,
  categories: [
    { category: 'LEARNING', count: 1, completed_count: 0 },
    { category: 'HEALTH', count: 1, completed_count: 1 },
  ],
  priorities: [
    { priority: 'HIGH', count: 1 },
    { priority: 'MEDIUM', count: 1 },
  ],
  statuses: [
    { status: 'IN_PROGRESS', count: 1 },
    { status: 'COMPLETED', count: 1 },
  ],
  recent_completions: [mockGoals[1]],
  upcoming_deadlines: [mockGoals[0]],
  daily_planning_completion_rate: 100,
  weekly_planning_completion_rate: 100,
};

const mockPlanningSummary: PlanningPeriodSummary = {
  period_type: 'DAILY',
  period_date: '2026-11-11',
  total_objectives: 1,
  completed_objectives: 0,
  completion_rate: 0,
  objectives: [
    {
      id: 'obj-1',
      user_id: 'user-1',
      goal_id: 'goal-1',
      goal_title: 'Learn Distributed Systems',
      task_id: null,
      task_title: null,
      title: 'Review Raft leader election logs',
      description: null,
      period_type: 'DAILY',
      period_date: '2026-11-11',
      priority: 'MEDIUM',
      is_completed: false,
      completed_at: null,
      order_index: 0,
      created_at: '2026-11-11T00:00:00Z',
      updated_at: '2026-11-11T00:00:00Z',
    },
  ],
};

describe('GoalsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(goalsApi.listGoals).mockResolvedValue({
      items: mockGoals,
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    vi.mocked(goalsApi.getAnalytics).mockResolvedValue(mockAnalytics);
    vi.mocked(goalsApi.getPlanningSummary).mockResolvedValue(mockPlanningSummary);
    vi.mocked(tasksApi.listTasks).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    vi.mocked(projectsApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
  });

  it('renders goals, analytics summary, and planning board', async () => {
    render(
      <MemoryRouter>
        <GoalsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Strategic Goals & Planning')).toBeInTheDocument();
    expect(screen.getByText('Learn Distributed Systems')).toBeInTheDocument();
    expect(screen.getByText('Run Marathon 2026')).toBeInTheDocument();

    // Analytics KPIs
    expect(screen.getByText('Active Goals')).toBeInTheDocument();
    expect(screen.getByText('Across all open goals')).toBeInTheDocument();

    // Planning Board
    expect(screen.getByText('Planning Alignment')).toBeInTheDocument();
    expect(screen.getByText('Review Raft leader election logs')).toBeInTheDocument();
  });

  it('filters goals by search keyword', async () => {
    render(
      <MemoryRouter>
        <GoalsPage />
      </MemoryRouter>
    );

    await screen.findByText('Learn Distributed Systems');

    // Search filter
    const searchInput = screen.getByPlaceholderText('Search goals...');
    fireEvent.change(searchInput, { target: { value: 'Marathon' } });

    expect(screen.getByText('Run Marathon 2026')).toBeInTheDocument();
    expect(screen.queryByText('Learn Distributed Systems')).not.toBeInTheDocument();

    // Reset search
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Learn Distributed Systems')).toBeInTheDocument();
  });

  it('opens goal detail modal and toggles milestone status', async () => {
    vi.mocked(goalsApi.getGoal).mockResolvedValue(mockGoals[0]);
    vi.mocked(goalsApi.updateMilestone).mockResolvedValue({
      ...mockGoals[0].milestones[1],
      is_completed: true,
    });

    render(
      <MemoryRouter>
        <GoalsPage />
      </MemoryRouter>
    );

    const goalCard = await screen.findByText('Learn Distributed Systems');
    fireEvent.click(goalCard);

    // Detail modal opens
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Read Raft paper')).toBeInTheDocument();
    expect(screen.getByText('Implement Raft consensus in Go')).toBeInTheDocument();
  });

  it('creates a new goal through GoalFormModal', async () => {
    vi.mocked(goalsApi.createGoal).mockResolvedValue({
      ...mockGoals[0],
      id: 'goal-3',
      title: 'Build Distributed Key-Value Store',
    });

    render(
      <MemoryRouter>
        <GoalsPage />
      </MemoryRouter>
    );

    await screen.findByText('Strategic Goals & Planning');
    const newGoalBtn = screen.getByRole('button', { name: /New Strategic Goal/i });
    fireEvent.click(newGoalBtn);

    expect(screen.getByText('Create New Goal')).toBeInTheDocument();
    const titleInput = screen.getByPlaceholderText('e.g. Master Rust Concurrency Patterns');
    fireEvent.change(titleInput, { target: { value: 'Build Distributed Key-Value Store' } });

    const submitBtn = screen.getByRole('button', { name: 'Create Goal' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(goalsApi.createGoal).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Build Distributed Key-Value Store',
        })
      );
    });
  });
});
