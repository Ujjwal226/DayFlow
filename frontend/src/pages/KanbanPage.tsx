import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { tasksApi } from '../api/tasks';
import { projectsApi } from '../api/projects';
import { categoriesApi } from '../api/categories';
import { tagsApi } from '../api/tags';
import { Task, TaskCreatePayload, TaskStatus } from '../types/task';
import { Project } from '../types/project';
import { Category } from '../types/category';
import { Tag } from '../types/tag';
import { KanbanFiltersState } from '../types/kanban';
import { KanbanToolbar } from '../components/kanban/KanbanToolbar';
import { KanbanBoard } from '../components/kanban/KanbanBoard';
import { TaskFormModal } from '../components/tasks/TaskForm';
import {
  Kanban as KanbanIcon,
  Layers,
  Calendar,
  CheckSquare,
  LogOut,
  AlertCircle,
  Folder,
} from 'lucide-react';

export const KanbanPage: React.FC = () => {
  const { logout, isLoading: authLoading } = useAuth();

  // Data state
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Optimistic update state
  const [updatingTaskIds, setUpdatingTaskIds] = useState<Set<string>>(new Set());

  // Task creation/editing modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [prefillStatus, setPrefillStatus] = useState<TaskStatus>('TODO');

  // Filter state
  const [filters, setFilters] = useState<KanbanFiltersState>({
    search: '',
    projectId: 'ALL',
    categoryId: 'ALL',
    priority: 'ALL',
    recurringOnly: false,
  });

  // Load initial data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [tasksRes, projectsRes, categoriesRes, tagsRes] = await Promise.all([
        tasksApi.listTasks({ page: 1, page_size: 100, is_archived: false }),
        projectsApi.list({ page_size: 100 }),
        categoriesApi.listCategories(),
        tagsApi.listTags(),
      ]);

      setTasks(tasksRes.items);
      setProjects(projectsRes.items);
      setCategories(categoriesRes);
      setTags(tagsRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load Kanban board data.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Projects map for quick lookup
  const projectsMap = useMemo(() => {
    const map = new Map<string, Project>();
    projects.forEach((p) => map.set(p.id, p));
    return map;
  }, [projects]);

  // Filter tasks client-side
  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      // Search
      if (filters.search.trim()) {
        const query = filters.search.toLowerCase();
        const matchesTitle = t.title.toLowerCase().includes(query);
        const matchesDesc = t.description?.toLowerCase().includes(query) ?? false;
        if (!matchesTitle && !matchesDesc) return false;
      }

      // Project filter
      if (filters.projectId === 'NO_PROJECT') {
        if (t.project_id) return false;
      } else if (filters.projectId !== 'ALL') {
        if (t.project_id !== filters.projectId) return false;
      }

      // Category filter
      if (filters.categoryId !== 'ALL') {
        if (t.category_id !== filters.categoryId) return false;
      }

      // Priority filter
      if (filters.priority !== 'ALL') {
        if (t.priority !== filters.priority) return false;
      }

      // Recurring only
      if (filters.recurringOnly) {
        if (!t.recurring_task_id) return false;
      }

      return true;
    });
  }, [tasks, filters]);

  // Filter setters
  const handleFilterChange = <K extends keyof KanbanFiltersState>(
    key: K,
    value: KanbanFiltersState[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      projectId: 'ALL',
      categoryId: 'ALL',
      priority: 'ALL',
      recurringOnly: false,
    });
  };

  // Drag and drop / Status change with optimistic updates and rollback
  const handleStatusChange = async (taskId: string, targetStatus: TaskStatus) => {
    const originalTask = tasks.find((t) => t.id === taskId);
    if (!originalTask || originalTask.status === targetStatus) return;

    // Prevent duplicate requests
    if (updatingTaskIds.has(taskId)) return;

    // Mark as updating
    setUpdatingTaskIds((prev) => new Set(prev).add(taskId));

    // Optimistically update UI
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: targetStatus } : t))
    );

    try {
      await tasksApi.updateTask(taskId, { status: targetStatus });
    } catch {
      // Rollback on failure
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: originalTask.status } : t))
      );
      setError(`Failed to update status for "${originalTask.title}". Reverted change.`);
    } finally {
      setUpdatingTaskIds((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }
  };

  // Open task creator
  const handleAddTask = (status: TaskStatus = 'TODO') => {
    setEditingTask(null);
    setPrefillStatus(status);
    setIsModalOpen(true);
  };

  // Open task editor
  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setIsModalOpen(true);
  };

  // Delete task
  const handleDeleteTask = async (task: Task) => {
    if (!window.confirm(`Are you sure you want to delete "${task.title}"?`)) return;

    try {
      await tasksApi.deleteTask(task.id);
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
    } catch {
      setError(`Failed to delete "${task.title}".`);
    }
  };

  // Handle task modal submit (create or edit)
  const handleTaskSubmit = async (payload: TaskCreatePayload) => {
    if (editingTask) {
      const updated = await tasksApi.updateTask(editingTask.id, payload);
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } else {
      const created = await tasksApi.createTask({
        ...payload,
        status: prefillStatus,
      });
      setTasks((prev) => [created, ...prev]);
    }
    setIsModalOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navigation Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
                DF
              </div>
              <span className="font-semibold text-lg tracking-tight text-white">DayFlow</span>
            </Link>

            <nav className="hidden sm:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/calendar"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Calendar</span>
              </Link>
              <Link
                to="/kanban"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <KanbanIcon className="w-3.5 h-3.5" />
                <span>Kanban</span>
              </Link>
              <Link
                to="/notes"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Notes</span>
              </Link>
              <Link
                to="/tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
              <Link
                to="/projects"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Folder className="w-3.5 h-3.5" />
                <span>Projects</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              disabled={authLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-300 hover:text-white text-xs font-medium transition flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-300 font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Toolbar & Filters */}
        <KanbanToolbar
          filters={filters}
          onFilterChange={handleFilterChange}
          onResetFilters={handleResetFilters}
          projects={projects}
          categories={categories}
          totalTasks={tasks.length}
          filteredTasksCount={filteredTasks.length}
          onNewTask={() => handleAddTask('TODO')}
          onRefresh={loadData}
          isLoading={isLoading}
        />

        {/* Board View */}
        {isLoading && tasks.length === 0 ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500" />
          </div>
        ) : (
          <KanbanBoard
            tasks={filteredTasks}
            projectsMap={projectsMap}
            onEditTask={handleEditTask}
            onDeleteTask={handleDeleteTask}
            onDropTask={handleStatusChange}
            onAddTask={handleAddTask}
            updatingTaskIds={updatingTaskIds}
          />
        )}
      </main>

      {/* Task Creation & Editing Modal */}
      <TaskFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleTaskSubmit}
        initialTask={editingTask}
        categories={categories}
        tags={tags}
      />
    </div>
  );
};
