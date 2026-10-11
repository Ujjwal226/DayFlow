import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plus,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-react';
import { tasksApi } from '../lib/api';
import type { Task, TaskCreate, TaskUpdate, TaskStatus, Category, Priority } from '../types/api';
import { TaskCard } from '../components/tasks/TaskCard';
import { TaskModal } from '../components/tasks/TaskModal';
import { DeleteConfirmModal } from '../components/tasks/DeleteConfirmModal';
import { toast } from 'sonner';

export const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<TaskStatus | 'all'>('all');
  const [selectedCategory, setSelectedCategory] = useState<Category | 'all'>('all');
  const [selectedPriority, setSelectedPriority] = useState<Priority | 'all'>('all');

  // Modals state
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState<Task | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);

  const fetchTasks = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // Build API filters based on selected items
      const filters: {
        status?: TaskStatus;
        category?: Category;
        priority?: Priority;
        limit?: number;
      } = { limit: 100 };

      if (selectedStatus !== 'all') filters.status = selectedStatus;
      if (selectedCategory !== 'all') filters.category = selectedCategory;
      if (selectedPriority !== 'all') filters.priority = selectedPriority;

      const data = await tasksApi.list(filters);
      setTasks(data.tasks);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(msg);
      toast.error('Error loading tasks: ' + msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedStatus, selectedCategory, selectedPriority]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Client-side text search on title & description
  const filteredTasks = useMemo(() => {
    if (!searchQuery.trim()) return tasks;
    const q = searchQuery.toLowerCase();
    return tasks.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        (t.description && t.description.toLowerCase().includes(q))
    );
  }, [tasks, searchQuery]);

  const hasActiveFilters =
    searchQuery.trim() !== '' ||
    selectedStatus !== 'all' ||
    selectedCategory !== 'all' ||
    selectedPriority !== 'all';

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedStatus('all');
    setSelectedCategory('all');
    setSelectedPriority('all');
  };

  // Task actions
  const handleCompleteTask = async (id: number) => {
    try {
      const updated = await tasksApi.complete(id);
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
      toast.success('Task marked as completed!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error completing task';
      toast.error(msg);
    }
  };

  const handleSaveTask = async (data: TaskCreate | TaskUpdate) => {
    if (taskToEdit) {
      const updated = await tasksApi.update(taskToEdit.id, data as TaskUpdate);
      setTasks((prev) => prev.map((t) => (t.id === taskToEdit.id ? updated : t)));
      toast.success('Task updated successfully!');
    } else {
      const created = await tasksApi.create(data as TaskCreate);
      setTasks((prev) => [created, ...prev]);
      toast.success('Task created successfully!');
    }
  };

  const handleDeleteTask = async (id: number) => {
    try {
      await tasksApi.delete(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      toast.success('Task deleted successfully');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error deleting task';
      toast.error(msg);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            My Tasks
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Organize, filter, and track all your scheduled items.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => fetchTasks(true)}
            disabled={refreshing}
            className="p-2.5 rounded-xl border border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
            title="Refresh tasks"
            aria-label="Refresh tasks"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            type="button"
            onClick={() => {
              setTaskToEdit(null);
              setIsTaskModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 active:bg-violet-800 text-white font-medium text-sm shadow-lg shadow-violet-600/25 transition-all focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Add Task</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
            <input
              type="text"
              placeholder="Search by title or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]/60 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Status select */}
          <div className="flex flex-wrap sm:flex-nowrap gap-2">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as TaskStatus | 'all')}
              className="px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
              aria-label="Filter by status"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>

            {/* Category select */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as Category | 'all')}
              className="px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
              aria-label="Filter by category"
            >
              <option value="all">All Categories</option>
              <option value="work">Work</option>
              <option value="personal">Personal</option>
              <option value="learning">Learning</option>
              <option value="health">Health</option>
              <option value="other">Other</option>
            </select>

            {/* Priority select */}
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value as Priority | 'all')}
              className="px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
              aria-label="Filter by priority"
            >
              <option value="all">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {hasActiveFilters && (
              <button
                type="button"
                onClick={resetFilters}
                className="px-3 py-2 rounded-xl border border-rose-500/20 text-rose-500 hover:bg-rose-500/10 text-xs font-semibold flex items-center space-x-1 transition-colors"
                title="Reset all filters"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Count summary */}
        <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] pt-1">
          <span>
            Showing <strong className="text-[var(--text-primary)]">{filteredTasks.length}</strong> tasks
          </span>
          {hasActiveFilters && (
            <span className="flex items-center space-x-1 text-violet-400">
              <Filter className="w-3 h-3" />
              <span>Filters applied</span>
            </span>
          )}
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-16 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)]">
            <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-2" />
            <p className="text-sm text-[var(--text-secondary)]">Fetching tasks...</p>
          </div>
        ) : error ? (
          <div className="p-8 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-center">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
            <p className="text-sm text-rose-500 font-medium">{error}</p>
            <button
              type="button"
              onClick={() => fetchTasks()}
              className="mt-3 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-12 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-500/10 text-violet-500 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">
              {hasActiveFilters ? 'No tasks match your filters' : 'No tasks yet'}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto">
              {hasActiveFilters
                ? 'Try adjusting your search query, status, priority, or category filters.'
                : 'Your task list is empty. Create your first task to get started.'}
            </p>
            {hasActiveFilters ? (
              <button
                type="button"
                onClick={resetFilters}
                className="px-4 py-2 rounded-xl border border-[var(--bg-border)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] text-xs font-medium transition-colors"
              >
                Clear Filters
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setTaskToEdit(null);
                  setIsTaskModalOpen(true);
                }}
                className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium shadow-md shadow-violet-600/20 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Create Task</span>
              </button>
            )}
          </div>
        ) : (
          filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onComplete={handleCompleteTask}
              onEdit={(t) => {
                setTaskToEdit(t);
                setIsTaskModalOpen(true);
              }}
              onDelete={(t) => setTaskToDelete(t)}
            />
          ))
        )}
      </div>

      {/* Task Modal (Create / Edit) */}
      <TaskModal
        isOpen={isTaskModalOpen}
        onClose={() => {
          setIsTaskModalOpen(false);
          setTaskToEdit(null);
        }}
        taskToEdit={taskToEdit}
        onSubmit={handleSaveTask}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!taskToDelete}
        onClose={() => setTaskToDelete(null)}
        task={taskToDelete}
        onConfirm={handleDeleteTask}
      />
    </div>
  );
};
