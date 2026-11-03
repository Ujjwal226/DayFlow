import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTasks } from '../hooks/useTasks';
import { Task, TaskCreatePayload } from '../types/task';
import { TaskStatisticsCard } from '../components/tasks/TaskStatistics';
import { TaskSearch } from '../components/tasks/TaskSearch';
import { TaskFilters } from '../components/tasks/TaskFilters';
import { TaskList } from '../components/tasks/TaskList';
import { TaskFormModal } from '../components/tasks/TaskForm';
import {
  Plus,
  ChevronLeft,
  ChevronRight,
  LogOut,
  LayoutDashboard,
  CheckSquare,
  AlertCircle,
} from 'lucide-react';

export const TasksPage: React.FC = () => {
  const { logout } = useAuth();
  const {
    tasks,
    total,
    totalPages,
    statistics,
    filters,
    setFilters,
    isLoading,
    error,
    createTask,
    updateTask,
    deleteTask,
    duplicateTask,
    archiveTask,
    restoreTask,
  } = useTasks();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleCreateOpen = () => {
    setEditingTask(null);
    setIsModalOpen(true);
  };

  const handleEditOpen = (task: Task) => {
    setEditingTask(task);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (payload: TaskCreatePayload) => {
    if (editingTask) {
      await updateTask(editingTask.id, payload);
    } else {
      await createTask(payload);
    }
  };

  const handleArchiveToggle = async (taskId: string, isArchived: boolean) => {
    if (isArchived) {
      await restoreTask(taskId);
    } else {
      await archiveTask(taskId);
    }
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirmId) {
      await deleteTask(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
                DF
              </div>
              <span className="font-semibold text-lg tracking-tight text-white">
                DayFlow
              </span>
            </Link>

            <nav className="hidden sm:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/tasks"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Task Workspace */}
      <main className="max-w-6xl mx-auto px-6 py-8 flex-1 w-full">
        {/* Header & Create Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <span>Task Management</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
                {total} tasks
              </span>
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Organize, track, and accomplish your personal priorities.
            </p>
          </div>

          <button
            onClick={handleCreateOpen}
            className="px-4 py-2.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-1.5 shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>Create Task</span>
          </button>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Aggregate Statistics */}
        <TaskStatisticsCard stats={statistics} isLoading={isLoading && !statistics} />

        {/* Search & Filter Bar */}
        <div className="space-y-3 mb-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <TaskSearch
              value={filters.search || ''}
              onChange={(val) => setFilters({ ...filters, search: val, page: 1 })}
            />
          </div>

          <TaskFilters
            filters={filters}
            onChange={(newFilters) => setFilters(newFilters)}
            onReset={() =>
              setFilters({
                page: 1,
                page_size: 20,
                is_archived: false,
                sort_by: 'created_at',
                sort_order: 'desc',
              })
            }
          />
        </div>

        {/* Task List Component */}
        <TaskList
          tasks={tasks}
          isLoading={isLoading}
          onEdit={handleEditOpen}
          onDuplicate={duplicateTask}
          onArchiveToggle={handleArchiveToggle}
          onDelete={(id) => setDeleteConfirmId(id)}
          onCreateClick={handleCreateOpen}
        />

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="mt-8 flex items-center justify-between border-t border-slate-800 pt-4 text-xs text-slate-400">
            <div>
              Showing page {filters.page || 1} of {totalPages} ({total} items total)
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={(filters.page || 1) <= 1}
                onClick={() =>
                  setFilters({ ...filters, page: Math.max(1, (filters.page || 1) - 1) })
                }
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none transition flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                disabled={(filters.page || 1) >= totalPages}
                onClick={() =>
                  setFilters({ ...filters, page: (filters.page || 1) + 1 })
                }
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:pointer-events-none transition flex items-center gap-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Task Creation / Editing Modal */}
      <TaskFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleFormSubmit}
        initialTask={editingTask}
      />

      {/* Delete Confirmation Dialog */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-3xl p-6 text-slate-100 shadow-2xl">
            <h3 className="text-base font-bold text-white">Delete Task?</h3>
            <p className="text-xs text-slate-400 mt-2">
              Are you sure you want to delete this task? This action cannot be undone.
            </p>
            <div className="mt-5 flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-3.5 py-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-1.5 rounded-xl bg-rose-500 hover:bg-rose-400 text-white text-xs font-semibold transition shadow-lg shadow-rose-500/20"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
