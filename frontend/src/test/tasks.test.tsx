import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { TaskFormModal } from '../components/tasks/TaskForm';
import { TaskList } from '../components/tasks/TaskList';
import { TaskFilters } from '../components/tasks/TaskFilters';
import { TaskSearch } from '../components/tasks/TaskSearch';
import { TaskPriorityBadge } from '../components/tasks/TaskPriorityBadge';
import { TaskStatusBadge } from '../components/tasks/TaskStatusBadge';
import { CategoryBadge } from '../components/categories/CategoryBadge';
import { TagBadge } from '../components/tags/TagBadge';
import { SubtaskProgress } from '../components/tasks/SubtaskProgress';
import { SubtaskList } from '../components/tasks/SubtaskList';
import { Task } from '../types/task';
import { Category } from '../types/category';
import { Tag } from '../types/tag';
import { Subtask } from '../types/subtask';

const mockCategory: Category = {
  id: 'cat-1',
  user_id: 'user-1',
  name: 'Work',
  description: 'Work category',
  color: '#10B981',
  icon: 'briefcase',
  task_count: 3,
  created_at: '2026-11-04T00:00:00Z',
  updated_at: '2026-11-04T00:00:00Z',
};

const mockTag: Tag = {
  id: 'tag-1',
  user_id: 'user-1',
  name: 'frontend',
  color: '#0D9488',
  task_count: 2,
  created_at: '2026-11-04T00:00:00Z',
  updated_at: '2026-11-04T00:00:00Z',
};

const mockSubtask: Subtask = {
  id: 'sub-1',
  user_id: 'user-1',
  parent_task_id: '123e4567-e89b-12d3-a456-426614174000',
  title: 'Child subtask 1',
  description: null,
  status: 'COMPLETED',
  priority: 'MEDIUM',
  start_date: null,
  due_date: null,
  completed_at: null,
  is_archived: false,
  is_overdue: false,
  created_at: '2026-11-04T00:00:00Z',
  updated_at: '2026-11-04T00:00:00Z',
};

const mockTask: Task = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  user_id: 'user-uuid-1',
  parent_task_id: null,
  category_id: mockCategory.id,
  category: mockCategory,
  tags: [mockTag],
  title: 'Test Task Alpha',
  description: 'Detailed description for testing',
  status: 'TODO',
  priority: 'HIGH',
  start_date: '2026-11-04T10:00:00Z',
  due_date: '2026-11-06T10:00:00Z',
  completed_at: null,
  is_archived: false,
  is_overdue: false,
  progress: {
    total_subtasks: 2,
    completed_subtasks: 1,
    remaining_subtasks: 1,
    progress_percentage: 50.0,
  },
  subtasks: [mockSubtask],
  created_at: '2026-11-04T08:00:00Z',
  updated_at: '2026-11-04T08:00:00Z',
};

describe('Task Management UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('TaskFormModal', () => {
    it('validates empty title and submits valid payload with category and tags', async () => {
      const user = userEvent.setup();
      const handleSubmit = vi.fn().mockResolvedValue(undefined);
      const handleClose = vi.fn();

      render(
        <TaskFormModal
          isOpen={true}
          onClose={handleClose}
          onSubmit={handleSubmit}
          categories={[mockCategory]}
          tags={[mockTag]}
        />
      );

      expect(screen.getByText('Create New Task')).toBeInTheDocument();

      const titleInput = screen.getByPlaceholderText(/Finalize quarterly budget forecast/i);
      const submitBtn = screen.getByRole('button', { name: /Create Task/i });

      // Click without title
      await user.click(submitBtn);

      // Fill title, select category and tag
      await user.type(titleInput, 'New Automated Task');

      const catSelect = screen.getByLabelText(/Category \(Optional\)/i);
      await user.selectOptions(catSelect, mockCategory.id);

      const tagBtn = screen.getByRole('button', { name: `#${mockTag.name}` });
      await user.click(tagBtn);

      await user.click(submitBtn);

      await waitFor(() => {
        expect(handleSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'New Automated Task',
            priority: 'MEDIUM',
            status: 'TODO',
            category_id: mockCategory.id,
            tag_ids: [mockTag.id],
          })
        );
      });
    });

    it('validates due date earlier than start date', async () => {
      const user = userEvent.setup();
      const handleSubmit = vi.fn().mockResolvedValue(undefined);
      const handleClose = vi.fn();

      render(
        <TaskFormModal
          isOpen={true}
          onClose={handleClose}
          onSubmit={handleSubmit}
        />
      );

      const titleInput = screen.getByPlaceholderText(/Finalize quarterly budget forecast/i);
      await user.type(titleInput, 'Invalid Date Task');

      // Set start date and due date
      const startDateInput = screen.getByLabelText(/Start Date/i);
      const dueDateInput = screen.getByLabelText(/Due Date/i);

      await user.type(startDateInput, '2026-11-06T12:00');
      await user.type(dueDateInput, '2026-11-04T12:00');

      const submitBtn = screen.getByRole('button', { name: /Create Task/i });
      await user.click(submitBtn);

      expect(await screen.findByText('Due date cannot be earlier than start date.')).toBeInTheDocument();
      expect(handleSubmit).not.toHaveBeenCalled();
    });
  });

  describe('TaskList and TaskCard with Categories & Tags', () => {
    it('renders task list with cards, category badge, tags and fires quick actions', async () => {
      const user = userEvent.setup();
      const onEdit = vi.fn();
      const onDuplicate = vi.fn();
      const onArchiveToggle = vi.fn();
      const onDelete = vi.fn();

      render(
        <BrowserRouter>
          <TaskList
            tasks={[mockTask]}
            isLoading={false}
            onEdit={onEdit}
            onDuplicate={onDuplicate}
            onArchiveToggle={onArchiveToggle}
            onDelete={onDelete}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Test Task Alpha')).toBeInTheDocument();
      expect(screen.getByText('Detailed description for testing')).toBeInTheDocument();
      expect(screen.getByText(mockCategory.name)).toBeInTheDocument();
      expect(screen.getByText(`#${mockTag.name}`)).toBeInTheDocument();

      // Quick action buttons
      const editBtn = screen.getByTitle('Edit task');
      await user.click(editBtn);
      expect(onEdit).toHaveBeenCalledWith(mockTask);

      const duplicateBtn = screen.getByTitle('Duplicate task');
      await user.click(duplicateBtn);
      expect(onDuplicate).toHaveBeenCalledWith(mockTask.id);

      const archiveBtn = screen.getByTitle('Archive task');
      await user.click(archiveBtn);
      expect(onArchiveToggle).toHaveBeenCalledWith(mockTask.id, false);

      const deleteBtn = screen.getByTitle('Delete task');
      await user.click(deleteBtn);
      expect(onDelete).toHaveBeenCalledWith(mockTask.id);
    });

    it('renders empty state when task array is empty', () => {
      render(
        <TaskList
          tasks={[]}
          isLoading={false}
          onEdit={vi.fn()}
          onDuplicate={vi.fn()}
          onArchiveToggle={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      expect(screen.getByText('No tasks found')).toBeInTheDocument();
    });
  });

  describe('Subtask Components', () => {
    it('renders SubtaskProgress and SubtaskList correctly', async () => {
      const user = userEvent.setup();
      const handleCreateSubtask = vi.fn().mockResolvedValue(undefined);
      const handleUpdateSubtask = vi.fn().mockResolvedValue(undefined);
      const handleDeleteSubtask = vi.fn().mockResolvedValue(undefined);

      render(
        <div>
          <SubtaskProgress progress={mockTask.progress} />
          <SubtaskList
            parentTaskId={mockTask.id}
            subtasks={[mockSubtask]}
            onCreateSubtask={handleCreateSubtask}
            onUpdateSubtask={handleUpdateSubtask}
            onDeleteSubtask={handleDeleteSubtask}
          />
        </div>
      );

      // Verify progress calculation rendering: 1/2 (50%)
      expect(screen.getByText(/1\/2 \(50%\)/i)).toBeInTheDocument();

      // Verify subtask item
      expect(screen.getByText('Child subtask 1')).toBeInTheDocument();

      // Add a subtask
      const addInput = screen.getByPlaceholderText(/Add a subtask/i);
      await user.type(addInput, 'Child subtask 2');
      const addBtn = screen.getByRole('button', { name: /Add/i });
      await user.click(addBtn);

      expect(handleCreateSubtask).toHaveBeenCalledWith(mockTask.id, { title: 'Child subtask 2' });
    });
  });

  describe('Badges, Search, and Filters', () => {
    it('renders priority, status, category, and tag badges correctly', () => {
      const { rerender } = render(<TaskPriorityBadge priority="URGENT" />);
      expect(screen.getByText('Urgent')).toBeInTheDocument();

      rerender(<TaskPriorityBadge priority="LOW" />);
      expect(screen.getByText('Low')).toBeInTheDocument();

      render(<TaskStatusBadge status="COMPLETED" />);
      expect(screen.getByText('Completed')).toBeInTheDocument();

      render(<CategoryBadge category={mockCategory} />);
      expect(screen.getByText('Work')).toBeInTheDocument();

      render(<TagBadge tag={mockTag} />);
      expect(screen.getByText('#frontend')).toBeInTheDocument();
    });

    it('triggers search input change', async () => {
      const user = userEvent.setup();
      const handleSearch = vi.fn();
      render(<TaskSearch value="" onChange={handleSearch} />);

      const searchInput = screen.getByPlaceholderText(/Search tasks by title/i);
      await user.type(searchInput, 'Budget');
      expect(handleSearch).toHaveBeenCalled();
    });

    it('handles filter selection changes including category and tags', async () => {
      const user = userEvent.setup();
      const handleFilterChange = vi.fn();
      const handleReset = vi.fn();

      render(
        <TaskFilters
          filters={{ status: undefined, priority: undefined, is_archived: false }}
          categories={[mockCategory]}
          tags={[mockTag]}
          onChange={handleFilterChange}
          onReset={handleReset}
        />
      );

      const statusSelect = screen.getByDisplayValue('All Statuses');
      await user.selectOptions(statusSelect, 'IN_PROGRESS');
      expect(handleFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'IN_PROGRESS' })
      );

      const catSelect = screen.getByDisplayValue('All Categories');
      await user.selectOptions(catSelect, mockCategory.id);
      expect(handleFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ category_id: mockCategory.id })
      );

      const resetBtn = screen.getByTitle('Reset filters');
      await user.click(resetBtn);
      expect(handleReset).toHaveBeenCalled();
    });
  });
});
