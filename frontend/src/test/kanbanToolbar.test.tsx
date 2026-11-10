import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KanbanToolbar } from '../components/kanban/KanbanToolbar';
import { KanbanFiltersState } from '../types/kanban';

describe('KanbanToolbar', () => {
  const defaultFilters: KanbanFiltersState = {
    search: '',
    projectId: 'ALL',
    categoryId: 'ALL',
    priority: 'ALL',
    recurringOnly: false,
  };

  it('renders search input and dropdown filters', () => {
    const onFilterChange = vi.fn();
    const onResetFilters = vi.fn();
    const onNewTask = vi.fn();
    const onRefresh = vi.fn();

    render(
      <KanbanToolbar
        filters={defaultFilters}
        onFilterChange={onFilterChange}
        onResetFilters={onResetFilters}
        projects={[{ id: 'p1', user_id: 'u1', name: 'Project Alpha', description: null, status: 'ACTIVE', priority: 'HIGH', start_date: null, due_date: null, color: null, is_archived: false, created_at: '', updated_at: '' }]}
        categories={[{ id: 'c1', user_id: 'u1', name: 'Design', description: null, color: '#F59E0B', icon: null, task_count: 3, created_at: '', updated_at: '' }]}
        totalTasks={10}
        filteredTasksCount={8}
        onNewTask={onNewTask}
        onRefresh={onRefresh}
        isLoading={false}
      />
    );

    expect(screen.getByPlaceholderText('Search tasks by title or description...')).toBeInTheDocument();
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('Design')).toBeInTheDocument();
    expect(screen.getByText(/Showing/)).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });

  it('triggers onFilterChange when selecting a project and searching', () => {
    const onFilterChange = vi.fn();

    render(
      <KanbanToolbar
        filters={defaultFilters}
        onFilterChange={onFilterChange}
        onResetFilters={vi.fn()}
        projects={[{ id: 'p1', user_id: 'u1', name: 'Project Alpha', description: null, status: 'ACTIVE', priority: 'HIGH', start_date: null, due_date: null, color: null, is_archived: false, created_at: '', updated_at: '' }]}
        categories={[]}
        totalTasks={5}
        filteredTasksCount={5}
        onNewTask={vi.fn()}
        onRefresh={vi.fn()}
        isLoading={false}
      />
    );

    // Search input
    fireEvent.change(screen.getByPlaceholderText('Search tasks by title or description...'), {
      target: { value: 'Refactor' },
    });
    expect(onFilterChange).toHaveBeenCalledWith('search', 'Refactor');

    // Project select
    fireEvent.change(screen.getByLabelText('Filter by project'), {
      target: { value: 'p1' },
    });
    expect(onFilterChange).toHaveBeenCalledWith('projectId', 'p1');
  });
});
