import React, { useState, useEffect, useCallback } from 'react';
import {
  History,
  ChevronLeft,
  ChevronRight,
  Calendar,
  CheckCircle2,
  Clock,
  CalendarClock,
  Trash2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Check,
} from 'lucide-react';
import { tasksApi } from '../lib/api';
import type { Task } from '../types/api';
import { PriorityBadge, CategoryBadge } from '../components/common/Badge';
import { TaskActivityModal } from '../components/tasks/TaskActivityModal';
import {
  todayISO,
  formatDate,
  formatTime,
  formatUTCDateTime,
  shiftDateISO,
} from '../lib/utils';
import { toast } from 'sonner';

export const HistoryPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>(todayISO());
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter & Activity Modal
  const [filterType, setFilterType] = useState<'all' | 'completed' | 'pending' | 'rescheduled' | 'deleted'>('all');
  const [selectedTaskForActivity, setSelectedTaskForActivity] = useState<Task | null>(null);

  const fetchHistory = useCallback(async (dateStr: string, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // Fetch historical tasks for the date (includes deleted and rescheduled)
      const data = await tasksApi.getHistoryByDate(dateStr, true);
      setTasks(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load task history';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory(selectedDate);
  }, [selectedDate, fetchHistory]);

  const handlePrevDay = () => {
    setSelectedDate((prev) => shiftDateISO(prev, -1));
  };

  const handleNextDay = () => {
    setSelectedDate((prev) => shiftDateISO(prev, 1));
  };

  const handleToday = () => {
    setSelectedDate(todayISO());
  };

  // Status and filter calculations
  const filteredTasks = tasks.filter((task) => {
    if (filterType === 'completed') return task.status === 'completed' && !task.deleted_at;
    if (filterType === 'pending') return task.status === 'pending' && !task.deleted_at;
    if (filterType === 'rescheduled') {
      return (
        task.original_scheduled_date &&
        task.original_scheduled_date !== task.scheduled_date
      );
    }
    if (filterType === 'deleted') return !!task.deleted_at;
    return true;
  });

  const completedCount = tasks.filter((t) => t.status === 'completed' && !t.deleted_at).length;
  const rescheduledCount = tasks.filter(
    (t) => t.original_scheduled_date && t.original_scheduled_date !== t.scheduled_date
  ).length;
  const deletedCount = tasks.filter((t) => !!t.deleted_at).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-violet-500 font-medium text-xs tracking-wider uppercase mb-1">
            <History className="w-4 h-4" />
            <span>Audit Trail & Records</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Task History & Date Navigator
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Navigate back in time, inspect original schedules, completion timestamps, and full task activity logs.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleToday}
            className="px-3 py-2 rounded-xl border border-[var(--bg-border)] text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
          >
            Go to Today
          </button>

          <button
            type="button"
            onClick={() => fetchHistory(selectedDate, true)}
            disabled={refreshing}
            className="p-2.5 rounded-xl border border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
            title="Refresh history"
            aria-label="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Date Navigation Bar */}
      <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 w-full md:w-auto justify-between md:justify-start">
          <button
            type="button"
            onClick={handlePrevDay}
            className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none border border-[var(--bg-border)]"
            title="Previous Day"
            aria-label="Previous Day"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-3 px-3 py-1.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)]">
            <Calendar className="w-4 h-4 text-violet-400" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {formatDate(selectedDate)}
            </span>
            {selectedDate === todayISO() && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 font-bold uppercase tracking-wider">
                Today
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleNextDay}
            className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none border border-[var(--bg-border)]"
            title="Next Day"
            aria-label="Next Day"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Date Picker Input */}
        <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
          <label htmlFor="history-date-picker" className="text-xs font-semibold uppercase text-[var(--text-secondary)]">
            Jump to date:
          </label>
          <input
            id="history-date-picker"
            type="date"
            value={selectedDate}
            onChange={(e) => {
              if (e.target.value) setSelectedDate(e.target.value);
            }}
            className="px-3 py-1.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
          />
        </div>
      </div>

      {/* Date Metrics & Filter Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-xl border transition-colors ${
              filterType === 'all'
                ? 'bg-violet-600 text-white border-violet-600 font-semibold shadow-sm'
                : 'border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
            }`}
          >
            All Recorded ({tasks.length})
          </button>

          <button
            type="button"
            onClick={() => setFilterType('completed')}
            className={`px-3 py-1.5 rounded-xl border transition-colors ${
              filterType === 'completed'
                ? 'bg-emerald-600 text-white border-emerald-600 font-semibold shadow-sm'
                : 'border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
            }`}
          >
            Completed ({completedCount})
          </button>

          <button
            type="button"
            onClick={() => setFilterType('rescheduled')}
            className={`px-3 py-1.5 rounded-xl border transition-colors ${
              filterType === 'rescheduled'
                ? 'bg-purple-600 text-white border-purple-600 font-semibold shadow-sm'
                : 'border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
            }`}
          >
            Rescheduled ({rescheduledCount})
          </button>

          <button
            type="button"
            onClick={() => setFilterType('deleted')}
            className={`px-3 py-1.5 rounded-xl border transition-colors ${
              filterType === 'deleted'
                ? 'bg-rose-600 text-white border-rose-600 font-semibold shadow-sm'
                : 'border-[var(--bg-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
            }`}
          >
            Deleted Archive ({deletedCount})
          </button>
        </div>

        <div className="text-[var(--text-secondary)] font-medium">
          Showing {filteredTasks.length} {filteredTasks.length === 1 ? 'record' : 'records'} for {formatDate(selectedDate)}
        </div>
      </div>

      {/* Historical Tasks List */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-16 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)]">
            <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-2" />
            <p className="text-sm text-[var(--text-secondary)]">Fetching historical records...</p>
          </div>
        ) : error ? (
          <div className="p-8 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-center">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
            <p className="text-sm text-rose-500 font-medium">{error}</p>
            <button
              type="button"
              onClick={() => fetchHistory(selectedDate)}
              className="mt-3 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-12 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-500/10 text-violet-400 flex items-center justify-center mx-auto">
              <Calendar className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">
              No tasks recorded for {formatDate(selectedDate)}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto">
              No tasks were scheduled, completed, rescheduled, or deleted on or from this date.
            </p>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const isCompleted = task.status === 'completed';
            const isDeleted = !!task.deleted_at;
            const isRescheduledFromThis =
              task.original_scheduled_date === selectedDate &&
              task.scheduled_date !== selectedDate;
            const isRescheduledToThis =
              task.scheduled_date === selectedDate &&
              task.original_scheduled_date &&
              task.original_scheduled_date !== selectedDate;

            return (
              <div
                key={task.id}
                className={`p-4 sm:p-5 rounded-2xl border transition-all duration-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  isDeleted
                    ? 'bg-rose-500/[0.03] border-rose-500/30'
                    : isCompleted
                    ? 'bg-[var(--bg-surface)]/90 border-[var(--bg-border)]/80 opacity-80'
                    : isRescheduledFromThis
                    ? 'bg-purple-500/[0.03] border-purple-500/30'
                    : 'bg-[var(--bg-surface)] border-[var(--bg-border)]'
                }`}
              >
                {/* Details */}
                <div className="flex items-start space-x-3.5 flex-1 min-w-0">
                  <div
                    className={`w-6 h-6 rounded-lg flex items-center justify-center border mt-0.5 shrink-0 ${
                      isDeleted
                        ? 'border-rose-500/50 bg-rose-500/10 text-rose-400'
                        : isCompleted
                        ? 'border-emerald-500 bg-emerald-500 text-white'
                        : 'border-[var(--text-secondary)]/50 bg-[var(--bg-elevated)] text-[var(--text-secondary)]'
                    }`}
                  >
                    {isDeleted ? (
                      <Trash2 className="w-3.5 h-3.5" />
                    ) : isCompleted ? (
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    ) : (
                      <Clock className="w-3.5 h-3.5" />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3
                        className={`text-base font-medium tracking-tight ${
                          isDeleted
                            ? 'text-rose-400 line-through'
                            : isCompleted
                            ? 'line-through text-[var(--text-secondary)]'
                            : 'text-[var(--text-primary)]'
                        }`}
                      >
                        {task.title}
                      </h3>

                      {/* Status Badges */}
                      {isDeleted && (
                        <span className="inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/20">
                          <Trash2 className="w-3 h-3 mr-1" /> Deleted
                        </span>
                      )}

                      {isRescheduledFromThis && (
                        <span className="inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-400 border border-purple-500/20">
                          <CalendarClock className="w-3 h-3 mr-1" /> Rescheduled to {task.scheduled_date}
                        </span>
                      )}

                      {isRescheduledToThis && (
                        <span className="inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-400 border border-purple-500/20">
                          <CalendarClock className="w-3 h-3 mr-1" /> Originally {task.original_scheduled_date}
                        </span>
                      )}
                    </div>

                    {task.description && (
                      <p className="text-sm text-[var(--text-secondary)] line-clamp-1 mb-2 font-normal">
                        {task.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)]">
                      <PriorityBadge priority={task.priority} />
                      <CategoryBadge category={task.category} />

                      {(task.start_time || task.end_time) && (
                        <span className="flex items-center space-x-1 pl-1">
                          <Clock className="w-3.5 h-3.5" />
                          <span>
                            {task.start_time ? formatTime(task.start_time) : ''}
                            {task.start_time && task.end_time ? ' - ' : ''}
                            {task.end_time ? formatTime(task.end_time) : ''}
                          </span>
                        </span>
                      )}

                      {task.completed_at && (
                        <span className="flex items-center space-x-1 pl-1 text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Completed: {formatUTCDateTime(task.completed_at)}</span>
                        </span>
                      )}

                      {task.deleted_at && (
                        <span className="flex items-center space-x-1 pl-1 text-rose-400">
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Deleted: {formatUTCDateTime(task.deleted_at)}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right: Activity button */}
                <div className="flex items-center space-x-2 self-end sm:self-center shrink-0">
                  <button
                    type="button"
                    onClick={() => setSelectedTaskForActivity(task)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-[var(--bg-border)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
                  >
                    <History className="w-3.5 h-3.5 text-violet-400" />
                    <span>View Activity Log</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Task Activity Modal */}
      <TaskActivityModal
        isOpen={!!selectedTaskForActivity}
        onClose={() => setSelectedTaskForActivity(null)}
        task={selectedTaskForActivity}
      />
    </div>
  );
};
