import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { KanbanPage } from '../pages/KanbanPage';
import { tasksApi } from '../api/tasks';
import { projectsApi } from '../api/projects';
import { categoriesApi } from '../api/categories';
import { tagsApi } from '../api/tags';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@dayflow.com', full_name: 'Test User' },
    logout: vi.fn(),
    logoutAll: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock('../api/tasks', () => ({
  tasksApi: {
    listTasks: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
  },
}));

vi.mock('../api/projects', () => ({
  projectsApi: {
    list: vi.fn(),
  },
}));

vi.mock('../api/categories', () => ({
  categoriesApi: {
    listCategories: vi.fn(),
  },
}));

vi.mock('../api/tags', () => ({
  tagsApi: {
    listTags: vi.fn(),
  },
}));

describe('KanbanPage', () => {
  const mockTasks = [
    {
      id: 'task-10',
      user_id: 'user-1',
      parent_task_id: null,
      category_id: null,
      project_id: null,
      recurring_task_id: null,
      title: 'Fix drag and drop edge cases',
      description: null,
      status: 'TODO',
      priority: 'HIGH',
      due_date: null,
      is_archived: false,
      is_overdue: false,
      created_at: '2026-11-10T00:00:00Z',
      updated_at: '2026-11-10T00:00:00Z',
    },
    {
      id: 'task-20',
      user_id: 'user-1',
      parent_task_id: null,
      category_id: null,
      project_id: null,
      recurring_task_id: null,
      title: 'Active In Progress Item',
      description: null,
      status: 'IN_PROGRESS',
      priority: 'MEDIUM',
      due_date: null,
      is_archived: false,
      is_overdue: false,
      created_at: '2026-11-10T00:00:00Z',
      updated_at: '2026-11-10T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (tasksApi.listTasks as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockTasks,
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (projectsApi.list as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (categoriesApi.listCategories as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tagsApi.listTags as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });

  it('renders all four Kanban columns and distributes tasks accurately', async () => {
    render(
      <MemoryRouter>
        <KanbanPage />
      </MemoryRouter>
    );

    // Verify 4 columns exist by heading level 3
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'To Do', level: 3 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'In Progress', level: 3 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Completed', level: 3 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Cancelled', level: 3 })).toBeInTheDocument();
    });

    // Check tasks in respective columns
    expect(screen.getByText('Fix drag and drop edge cases')).toBeInTheDocument();
    expect(screen.getByText('Active In Progress Item')).toBeInTheDocument();
  });

  it('handles drag drop status update and optimistically updates UI', async () => {
    (tasksApi.updateTask as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockTasks[0],
      status: 'IN_PROGRESS',
    });

    render(
      <MemoryRouter>
        <KanbanPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fix drag and drop edge cases')).toBeInTheDocument();
    });

    // Move task using keyboard dropdown (invokes same onStatusChange/handleStatusChange handler)
    const select = screen.getByLabelText('Change status for Fix drag and drop edge cases');
    fireEvent.change(select, { target: { value: 'IN_PROGRESS' } });

    expect(tasksApi.updateTask).toHaveBeenCalledWith('task-10', { status: 'IN_PROGRESS' });
  });

  it('rolls back optimistic update when task update fails', async () => {
    (tasksApi.updateTask as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network error')
    );

    render(
      <MemoryRouter>
        <KanbanPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fix drag and drop edge cases')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Change status for Fix drag and drop edge cases');
    fireEvent.change(select, { target: { value: 'COMPLETED' } });

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update status for "Fix drag and drop edge cases"/)
      ).toBeInTheDocument();
    });
  });
});
