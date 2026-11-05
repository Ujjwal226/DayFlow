import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useRecurringTasks } from '../hooks/useRecurringTasks';
import { categoriesApi } from '../api/categories';
import { projectsApi } from '../api/projects';
import { Category } from '../types/category';
import { Project } from '../types/project';
import {
  RecurringTask,
  RecurrenceFrequency,
  RecurringTaskCreatePayload,
  RecurringTaskUpdatePayload,
} from '../types/recurringTask';
import { RecurringTaskCard } from '../components/recurringTasks/RecurringTaskCard';
import { RecurringTaskFormModal } from '../components/recurringTasks/RecurringTaskForm';
import {
  Repeat,
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  LogOut,
  LayoutDashboard,
  CheckSquare,
  FolderKanban,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

export const RecurringTasksPage: React.FC = () => {
  const { logout } = useAuth();
  const {
    recurringTasks,
    total,
    page,
    totalPages,
    frequency,
    setFrequency,
    statusFilter,
    setStatusFilter,
    search,
    setSearch,
    isLoading,
    error,
    setPage,
    createRecurringTask,
    updateRecurringTask,
    deleteRecurringTask,
    pauseRecurringTask,
    resumeRecurringTask,
    stopRecurringTask,
    fetchRecurringTasks,
  } = useRecurringTasks();

  const [categories, setCategories] = useState<Category[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSeries, setEditingSeries] = useState<RecurringTask | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    const loadSupportData = async () => {
      try {
        const [catList, projList] = await Promise.all([
          categoriesApi.listCategories(),
          projectsApi.list({ page_size: 100 }),
        ]);
        setCategories(catList);
        setProjects(projList.items);
      } catch {
        // Silently tolerate support list failures
      }
    };
    loadSupportData();
  }, []);

  const handleOpenCreate = () => {
    setEditingSeries(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (series: RecurringTask) => {
    setEditingSeries(series);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (
    payload: RecurringTaskCreatePayload | RecurringTaskUpdatePayload
  ) => {
    if (editingSeries) {
      await updateRecurringTask(editingSeries.id, payload);
    } else {
      await createRecurringTask(payload as RecurringTaskCreatePayload);
    }
  };

  const confirmDelete = async () => {
    if (deleteConfirmId) {
      await deleteRecurringTask(deleteConfirmId);
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
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
              <Link
                to="/projects"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <FolderKanban className="w-3.5 h-3.5" />
                <span>Projects</span>
              </Link>
              <Link
                to="/recurring-tasks"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <Repeat className="w-3.5 h-3.5" />
                <span>Recurring Tasks</span>
              </Link>
              <Link
                to="/activity"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Activity</span>
              </Link>
              <Link
                to="/analytics"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Analytics</span>
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

      {/* Main Workspace */}
      <main className="max-w-6xl mx-auto px-6 py-8 flex-1 w-full space-y-6">
        {/* Header & Add Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <span>Recurring Tasks & Scheduling</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
                {total} series
              </span>
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Automate routine habits, recurring responsibilities, and team sync schedules.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchRecurringTasks()}
              className="p-2.5 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Refresh list"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={handleOpenCreate}
              className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              <span>Create Series</span>
            </button>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                placeholder="Search series by title or description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>

            {/* Frequency Filter */}
            <div>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as RecurrenceFrequency | '')}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Frequencies</option>
                <option value="DAILY">Daily</option>
                <option value="WEEKLY">Weekly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="YEARLY">Yearly</option>
                <option value="CUSTOM">Custom Interval</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) =>
                  setStatusFilter(e.target.value as 'all' | 'active' | 'paused' | 'stopped')
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="paused">Paused Only</option>
                <option value="stopped">Stopped Only</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="h-48 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse"
              />
            ))}
          </div>
        ) : recurringTasks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-800 p-12 text-center bg-slate-900/20">
            <Repeat className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white mb-1">No recurring tasks found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6">
              Create your first recurring task series to schedule automated reminders and task occurrences.
            </p>
            <button
              onClick={handleOpenCreate}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-xs transition inline-flex items-center gap-1.5 shadow-lg shadow-emerald-500/20"
            >
              <Plus className="w-4 h-4" />
              <span>Create Series</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recurringTasks.map((series) => (
              <RecurringTaskCard
                key={series.id}
                series={series}
                onEdit={handleOpenEdit}
                onPause={pauseRecurringTask}
                onResume={resumeRecurringTask}
                onStop={stopRecurringTask}
                onDelete={(id) => setDeleteConfirmId(id)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-800 pt-4 text-xs text-slate-400">
            <div>
              Showing page {page} of {totalPages}
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100">
            <h3 className="text-base font-bold text-white mb-2">Delete Recurring Task Series?</h3>
            <p className="text-xs text-slate-400 mb-6">
              This will permanently delete this recurring series configuration. Existing task occurrences generated previously will be preserved.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 rounded-xl border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-400 text-white font-semibold text-xs shadow-lg shadow-rose-500/20 transition"
              >
                Delete Series
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Form Modal */}
      <RecurringTaskFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleFormSubmit}
        initialSeries={editingSeries}
        categories={categories}
        projects={projects}
      />
    </div>
  );
};
