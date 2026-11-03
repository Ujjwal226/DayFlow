import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProjectsPage } from '../pages/ProjectsPage';
import { ProjectDetailsPage } from '../pages/ProjectDetailsPage';
import { ProjectCard } from '../components/projects/ProjectCard';
import { ProjectProgress } from '../components/projects/ProjectProgress';
import { ProjectFilters } from '../components/projects/ProjectFilters';
import { projectsApi } from '../api/projects';
import { Project } from '../types/project';

vi.mock('../api/projects');
vi.mock('../api/tasks');

const mockProject: Project = {
  id: 'proj-123',
  user_id: 'user-1',
  name: 'Mobile App Redesign',
  description: 'Design mobile views and responsive navbar',
  status: 'ACTIVE',
  priority: 'HIGH',
  start_date: '2026-06-01',
  due_date: '2026-06-30',
  color: '#3B82F6',
  is_archived: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  statistics: {
    total_tasks: 4,
    completed_tasks: 2,
    pending_tasks: 1,
    in_progress_tasks: 1,
    cancelled_tasks: 0,
    overdue_tasks: 0,
    completion_percentage: 50.0,
  },
};

describe('Project Management Frontend Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders ProjectCard correctly with status, priority, and progress', () => {
    render(
      <BrowserRouter>
        <ProjectCard
          project={mockProject}
          onEdit={vi.fn()}
          onArchive={vi.fn()}
          onRestore={vi.fn()}
          onDelete={vi.fn()}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Mobile App Redesign')).toBeInTheDocument();
    expect(screen.getByText(/Design mobile views/i)).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText(/2 of 4 tasks/i)).toBeInTheDocument();
  });

  it('renders ProjectProgress with correct percentages and labels', () => {
    render(<ProjectProgress completed={3} total={10} percentage={30.0} />);
    expect(screen.getByText('Project Progress')).toBeInTheDocument();
    expect(screen.getByText('30%')).toBeInTheDocument();
    expect(screen.getByText('3 of 10 tasks')).toBeInTheDocument();
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '30');
  });

  it('handles ProjectFilters inputs and reset', () => {
    const onSearchChange = vi.fn();
    const onStatusChange = vi.fn();
    const onPriorityChange = vi.fn();
    const onIsArchivedChange = vi.fn();
    const onReset = vi.fn();

    render(
      <ProjectFilters
        search=""
        onSearchChange={onSearchChange}
        status=""
        onStatusChange={onStatusChange}
        priority=""
        onPriorityChange={onPriorityChange}
        isArchived={false}
        onIsArchivedChange={onIsArchivedChange}
        onReset={onReset}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search projects...');
    fireEvent.change(searchInput, { target: { value: 'Redesign' } });
    expect(onSearchChange).toHaveBeenCalledWith('Redesign');

    const statusSelect = screen.getByLabelText('Status');
    fireEvent.change(statusSelect, { target: { value: 'ACTIVE' } });
    expect(onStatusChange).toHaveBeenCalledWith('ACTIVE');

    const resetBtn = screen.getByText('Reset Filters');
    fireEvent.click(resetBtn);
    expect(onReset).toHaveBeenCalled();
  });

  it('renders ProjectsPage with project list', async () => {
    vi.mocked(projectsApi.list).mockResolvedValue({
      items: [mockProject],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    render(
      <BrowserRouter>
        <ProjectsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Mobile App Redesign')).toBeInTheDocument();
    });
    expect(screen.getByText('+ New Project')).toBeInTheDocument();
  });

  it('renders ProjectsPage empty state when no projects exist', async () => {
    vi.mocked(projectsApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });

    render(
      <BrowserRouter>
        <ProjectsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/No projects created yet. Start organizing your work/i)
      ).toBeInTheDocument();
    });
  });

  it('renders ProjectDetailsPage with statistics and task list', async () => {
    vi.mocked(projectsApi.get).mockResolvedValue(mockProject);
    vi.mocked(projectsApi.getStatistics).mockResolvedValue(mockProject.statistics!);
    vi.mocked(projectsApi.listTasks).mockResolvedValue({
      items: [
        {
          id: 'task-1',
          user_id: 'user-1',
          parent_task_id: null,
          category_id: null,
          project_id: mockProject.id,
          title: 'Setup routing components',
          description: null,
          status: 'COMPLETED',
          priority: 'MEDIUM',
          start_date: null,
          due_date: null,
          completed_at: null,
          is_archived: false,
          is_overdue: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    render(
      <MemoryRouter initialEntries={['/projects/proj-123']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectDetailsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Mobile App Redesign')).toBeInTheDocument();
      expect(screen.getByText('Setup routing components')).toBeInTheDocument();
      expect(screen.getByText('Total Tasks')).toBeInTheDocument();
    });
  });
});
