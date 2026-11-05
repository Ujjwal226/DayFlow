import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { recurringTasksApi } from '../api/recurringTasks';
import { categoriesApi } from '../api/categories';
import { projectsApi } from '../api/projects';
import { RecurringTask } from '../types/recurringTask';
import { Category } from '../types/category';
import { Project } from '../types/project';
import { Task } from '../types/task';
import { RecurrenceBadge } from '../components/recurringTasks/RecurrenceBadge';
import { TaskPriorityBadge } from '../components/tasks/TaskPriorityBadge';
import { CategoryBadge } from '../components/categories/CategoryBadge';
import { OccurrenceList } from '../components/recurringTasks/OccurrenceList';
import { SkipOccurrenceDialog } from '../components/recurringTasks/SkipOccurrenceDialog';
import { RecurringTaskFormModal } from '../components/recurringTasks/RecurringTaskForm';
import {
  ArrowLeft,
  Calendar,
  Layers,
  Play,
  Pause,
  Square,
  Trash2,
  Edit2,
  CalendarX,
  Clock,
  AlertCircle,
  FolderKanban,
  Repeat,
} from 'lucide-react';

export const RecurringTaskDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [series, setSeries] = useState<RecurringTask | null>(null);
  const [occurrences, setOccurrences] = useState<Task[]>([]);
  const [totalOccurrences, setTotalOccurrences] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(0);

  const [categories, setCategories] = useState<Category[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isOccurrencesLoading, setIsOccurrencesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSkipModalOpen, setIsSkipModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isStopModalOpen, setIsStopModalOpen] = useState(false);

  const fetchSeries = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await recurringTasksApi.get(id);
      setSeries(data);
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(msg || 'Failed to load recurring task series.');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  const fetchOccurrences = useCallback(async () => {
    if (!id) return;
    setIsOccurrencesLoading(true);
    try {
      const res = await recurringTasksApi.listOccurrences(id, { page, page_size: pageSize });
      setOccurrences(res.items);
      setTotalOccurrences(res.total);
      setTotalPages(res.total_pages);
    } catch {
      // Tolerate occurrences listing failure
    } finally {
      setIsOccurrencesLoading(false);
    }
  }, [id, page, pageSize]);

  useEffect(() => {
    fetchSeries();
  }, [fetchSeries]);

  useEffect(() => {
    fetchOccurrences();
  }, [fetchOccurrences]);

  useEffect(() => {
    const loadSupportData = async () => {
      try {
        const [cats, projs] = await Promise.all([
          categoriesApi.listCategories(),
          projectsApi.list({ page_size: 100 }),
        ]);
        setCategories(cats);
        setProjects(projs.items);
      } catch {
        // Tolerate support load failures
      }
    };
    loadSupportData();
  }, []);

  const handlePause = async () => {
    if (!id) return;
    try {
      const updated = await recurringTasksApi.pause(id);
      setSeries(updated);
    } catch {
      // Handled
    }
  };

  const handleResume = async () => {
    if (!id) return;
    try {
      const updated = await recurringTasksApi.resume(id);
      setSeries(updated);
    } catch {
      // Handled
    }
  };

  const handleStop = async () => {
    if (!id) return;
    try {
      const updated = await recurringTasksApi.stop(id);
      setSeries(updated);
      setIsStopModalOpen(false);
    } catch {
      // Handled
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await recurringTasksApi.delete(id);
      navigate('/recurring-tasks');
    } catch {
      // Handled
    }
  };

  const handleSkipConfirm = async (skipDate: string, reason?: string) => {
    if (!id) return;
    const updated = await recurringTasksApi.skipOccurrence(id, { skip_date: skipDate, reason });
    setSeries(updated);
    await fetchOccurrences();
  };

  const handleEditSubmit = async (payload: Parameters<typeof recurringTasksApi.update>[1]) => {
    if (!id) return;
    const updated = await recurringTasksApi.update(id, payload);
    setSeries(updated);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error || !series) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
        <div className="max-w-4xl mx-auto space-y-4">
          <Link
            to="/recurring-tasks"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Recurring Tasks</span>
          </Link>
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error || 'Recurring task series not found.'}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-white">
      {/* Top Breadcrumb Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            to="/recurring-tasks"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Recurring Tasks</span>
          </Link>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {!series.is_stopped && (
              <>
                {series.is_active ? (
                  <button
                    onClick={handlePause}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
                  >
                    <Pause className="w-3.5 h-3.5 text-amber-400" />
                    <span>Pause</span>
                  </button>
                ) : (
                  <button
                    onClick={handleResume}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition flex items-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Resume</span>
                  </button>
                )}

                {series.next_occurrence_date && (
                  <button
                    onClick={() => setIsSkipModalOpen(true)}
                    className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-semibold border border-amber-500/30 transition flex items-center gap-1.5"
                  >
                    <CalendarX className="w-3.5 h-3.5" />
                    <span>Skip Next</span>
                  </button>
                )}

                <button
                  onClick={() => setIsStopModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>Stop</span>
                </button>
              </>
            )}

            <button
              onClick={() => setIsEditModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>

            <button
              onClick={() => setIsDeleteModalOpen(true)}
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
              title="Delete series"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Series Overview Card */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5 flex-wrap">
                <RecurrenceBadge frequency={series.frequency} interval={series.interval} />
                <TaskPriorityBadge priority={series.priority} />
                {series.category && <CategoryBadge category={series.category} />}
                {series.is_stopped ? (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                    Stopped
                  </span>
                ) : !series.is_active ? (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Paused
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Active
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {series.title}
              </h1>
            </div>
          </div>

          {series.description && (
            <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
              {series.description}
            </p>
          )}

          {/* Schedule stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                <span>Next Occurrence</span>
              </div>
              <div className="text-base font-bold text-white">
                {series.next_occurrence_date || 'None'}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <span>Generated Count</span>
              </div>
              <div className="text-base font-bold text-white">
                {series.occurrences_generated}
                {series.max_occurrences ? ` / ${series.max_occurrences}` : ''}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span>Start Date</span>
              </div>
              <div className="text-base font-bold text-white">{series.start_date}</div>
            </div>

            <div className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <FolderKanban className="w-3.5 h-3.5 text-amber-400" />
                <span>End Date</span>
              </div>
              <div className="text-base font-bold text-white">
                {series.end_date || 'No End Date'}
              </div>
            </div>
          </div>
        </div>

        {/* Generated Occurrences Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                <Repeat className="w-4 h-4 text-emerald-400" />
                <span>Generated Occurrences</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
                  {totalOccurrences} tasks
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Individual task instances generated from this template schedule.
              </p>
            </div>
          </div>

          <OccurrenceList
            occurrences={occurrences}
            total={totalOccurrences}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            isLoading={isOccurrencesLoading}
          />
        </div>
      </main>

      {/* Skip Occurrence Dialog */}
      <SkipOccurrenceDialog
        isOpen={isSkipModalOpen}
        onClose={() => setIsSkipModalOpen(false)}
        onConfirm={handleSkipConfirm}
        defaultDate={series.next_occurrence_date}
      />

      {/* Stop Confirmation Modal */}
      {isStopModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100">
            <h3 className="text-base font-bold text-white mb-2">Stop Recurrence Schedule?</h3>
            <p className="text-xs text-slate-400 mb-6">
              Stopping recurrence will permanently disable automated generation for this series. Existing occurrences will remain intact.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setIsStopModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={handleStop}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition"
              >
                Confirm Stop
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100">
            <h3 className="text-base font-bold text-white mb-2">Delete Recurring Task Series?</h3>
            <p className="text-xs text-slate-400 mb-6">
              This will remove the series template completely. Past occurrences that have already been created will remain in your tasks list.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setIsDeleteModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-400 text-white font-semibold text-xs shadow-lg shadow-rose-500/20 transition"
              >
                Delete Series
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Form Modal */}
      <RecurringTaskFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleEditSubmit}
        initialSeries={series}
        categories={categories}
        projects={projects}
      />
    </div>
  );
};
