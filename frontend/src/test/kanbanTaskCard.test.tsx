import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KanbanTaskCard } from '../components/kanban/KanbanTaskCard';
import { Task } from '../types/task';
import { Project } from '../types/project';

describe('KanbanTaskCard', () => {
  const mockTask: Task = {
    id: 'task-1',
    user_id: 'user-1',
    parent_task_id: null,
    category_id: 'cat-1',
    category: {
      id: 'cat-1',
      user_id: 'user-1',
      name: 'Engineering',
      description: null,
      color: '#3B82F6',
      icon: null,
      task_count: 5,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    project_id: 'proj-1',
    recurring_task_id: null,
    occurrence_date: null,
    occurrence_index: null,
    tags: [{ id: 'tag-1', user_id: 'user-1', name: 'frontend', color: '#10B981', task_count: 2, created_at: '', updated_at: '' }],
    title: 'Design Kanban Columns',
    description: 'Implement drag and drop columns for the board',
    status: 'TODO',
    priority: 'HIGH',
    start_date: null,
    due_date: '2026-11-20T10:00:00Z',
    completed_at: null,
    is_archived: false,
    is_overdue: false,
    progress: {
      total_subtasks: 3,
      completed_subtasks: 1,
      remaining_subtasks: 2,
      progress_percentage: 33,
    },
    created_at: '2026-11-10T00:00:00Z',
    updated_at: '2026-11-10T00:00:00Z',
  };

  const mockProject: Project = {
    id: 'proj-1',
    user_id: 'user-1',
    name: 'DayFlow Core',
    description: null,
    status: 'ACTIVE',
    priority: 'HIGH',
    start_date: null,
    due_date: null,
    color: '#10B981',
    is_archived: false,
    created_at: '',
    updated_at: '',
  };

  it('renders task details, priority, project, and tags accurately', () => {
    render(
      <KanbanTaskCard
        task={mockTask}
        project={mockProject}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
      />
    );

    expect(screen.getByText('Design Kanban Columns')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getByText('DayFlow Core')).toBeInTheDocument();
    expect(screen.getByText('#frontend')).toBeInTheDocument();
    expect(screen.getByText('1/3')).toBeInTheDocument();
  });

  it('supports keyboard-accessible status changes via select dropdown', () => {
    const onStatusChange = vi.fn();
    render(
      <KanbanTaskCard
        task={mockTask}
        project={mockProject}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={onStatusChange}
      />
    );

    const select = screen.getByLabelText('Change status for Design Kanban Columns');
    fireEvent.change(select, { target: { value: 'IN_PROGRESS' } });

    expect(onStatusChange).toHaveBeenCalledWith('task-1', 'IN_PROGRESS');
  });

  it('fires onEdit when clicking card title or edit button', () => {
    const onEdit = vi.fn();
    render(
      <KanbanTaskCard
        task={mockTask}
        project={mockProject}
        onEdit={onEdit}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('Design Kanban Columns'));
    expect(onEdit).toHaveBeenCalledWith(mockTask);

    fireEvent.click(screen.getByLabelText('Edit task Design Kanban Columns'));
    expect(onEdit).toHaveBeenCalledTimes(2);
  });
});
