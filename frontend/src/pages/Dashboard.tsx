import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plus,
  CheckCircle2,
  Clock,
  AlertCircle,
  ListTodo,
  TrendingUp,
  ArrowRight,
  Sparkles,
  CalendarDays,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { tasksApi } from '../lib/api';
import type { Task, TaskCreate, TaskReschedule, TaskUpdate } from '../types/api';
import { TaskCard } from '../components/tasks/TaskCard';
import { TaskModal } from '../components/tasks/TaskModal';
import { RescheduleModal } from '../components/tasks/RescheduleModal';
import { TaskActivityModal } from '../components/tasks/TaskActivityModal';
import { DeleteConfirmModal } from '../components/tasks/DeleteConfirmModal';
import { todayISO, formatDate, formatTime, isOverdue, isToday } from '../lib/utils';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState<Task | null>(null);
  const [taskToReschedule, setTaskToReschedule] = useState<Task | null>(null);
  const [taskForActivity, setTaskForActivity] = useState<Task | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);

  const fetchTasks = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const data = await tasksApi.list({ limit: 100 });
      setTasks(data.tasks);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(msg);
      toast.error('Failed to load dashboard data: ' + msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Derived metrics
  const today = todayISO();
  const todayDateObj = new Date();
  const formattedToday = todayDateObj.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const greeting = useMemo(() => {
    const hours = todayDateObj.getHours();
    if (hours < 12) return 'Good morning';
    if (hours < 18) return 'Good afternoon';
    return 'Good evening';
  }, [todayDateObj]);

  const {
    totalCount,
    completedCount,
    pendingCount,
    overdueCount,
    todayTasks,
    nextUpcomingTask,
    completionPercentage,
  } = useMemo(() => {
    const total = tasks.length;
    let completed = 0;
    let pending = 0;
    let overdue = 0;
    const todayList: Task[] = [];
    const upcomingCandidates: Task[] = [];

    tasks.forEach((task) => {
      if (task.status === 'completed') {
        completed++;
      } else {
        pending++;
        if (isOverdue(task.scheduled_date, task.status)) {
          overdue++;
        }
        if (task.scheduled_date >= today) {
          upcomingCandidates.push(task);
        }
      }

      if (isToday(task.scheduled_date)) {
        todayList.push(task);
      }
    });

    // Chronological order for today's tasks:
    // 1. Tasks with start_time sorted ascending
    // 2. Tasks without start_time (all-day/unscheduled time)
    // 3. Fallback to id
    todayList.sort((a, b) => {
      if (a.start_time && b.start_time) {
        return a.start_time.localeCompare(b.start_time);
      }
      if (a.start_time) return -1;
      if (b.start_time) return 1;
      return a.id - b.id;
    });

    // Next upcoming task: closest date, earliest start_time
    upcomingCandidates.sort((a, b) => {
      if (a.scheduled_date !== b.scheduled_date) {
        return a.scheduled_date.localeCompare(b.scheduled_date);
      }
      if (a.start_time && b.start_time) {
        return a.start_time.localeCompare(b.start_time);
      }
      if (a.start_time) return -1;
      if (b.start_time) return 1;
      return a.id - b.id;
    });

    const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

    return {
      totalCount: total,
      completedCount: completed,
      pendingCount: pending,
      overdueCount: overdue,
      todayTasks: todayList,
      nextUpcomingTask: upcomingCandidates[0] || null,
      completionPercentage: rate,
    };
  }, [tasks, today]);

  // Actions
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

  const handleReopenTask = async (id: number) => {
    try {
      const updated = await tasksApi.reopen(id);
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
      toast.success('Task reopened and returned to pending!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error reopening task';
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

  const handleReschedule = async (id: number, payload: TaskReschedule) => {
    try {
      const updated = await tasksApi.reschedule(id, payload);
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
      toast.success(`Task rescheduled to ${formatDate(payload.scheduled_date)}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reschedule task';
      toast.error(msg);
      throw err;
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
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header Greeting & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-violet-500 font-medium text-xs tracking-wider uppercase mb-1">
            <CalendarDays className="w-4 h-4" />
            <span>{formattedToday}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            {greeting}, ready to flow?
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Here is your daily productivity overview and schedule.
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

      {/* Summary Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Tasks */}
        <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm hover:border-violet-500/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Total Tasks</span>
            <div className="w-8 h-8 rounded-lg bg-violet-500/10 text-violet-500 flex items-center justify-center">
              <ListTodo className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mt-3">{totalCount}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">Managed in DayFlow</p>
        </div>

        {/* Pending Tasks */}
        <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm hover:border-amber-500/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Pending</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mt-3">{pendingCount}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">Requires action</p>
        </div>

        {/* Completed Tasks */}
        <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm hover:border-emerald-500/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Completed</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mt-3">{completedCount}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">{completionPercentage}% completion rate</p>
        </div>

        {/* Overdue Tasks */}
        <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm hover:border-rose-500/20 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Overdue</span>
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mt-3">{overdueCount}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">Past scheduled date</p>
        </div>
      </div>

      {/* Progress & Next Upcoming Task Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Completion Progress Indicator */}
        <div className="lg:col-span-1 p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold tracking-wide uppercase text-[var(--text-secondary)]">Daily Progress</h2>
              <TrendingUp className="w-4 h-4 text-violet-500" />
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-4xl font-extrabold text-[var(--text-primary)] tracking-tight">
                {completionPercentage}%
              </span>
              <span className="text-xs text-[var(--text-secondary)] font-medium">overall completed</span>
            </div>
            <div className="w-full bg-[var(--bg-elevated)] h-3 rounded-full mt-4 overflow-hidden border border-[var(--bg-border)]/50">
              <div
                className="bg-gradient-to-r from-violet-600 to-indigo-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-6">
            {completedCount} of {totalCount} tasks completed. Keep up the momentum!
          </p>
        </div>

        {/* Next Upcoming Task Spotlight */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-gradient-to-br from-violet-900/15 via-[var(--bg-surface)] to-[var(--bg-surface)] border border-violet-500/20 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-violet-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4" />
              <span>Next Upcoming Task</span>
            </div>
            {nextUpcomingTask ? (
              <div className="mt-2">
                <h3 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">
                  {nextUpcomingTask.title}
                </h3>
                {nextUpcomingTask.description && (
                  <p className="text-sm text-[var(--text-secondary)] mt-1 line-clamp-2">
                    {nextUpcomingTask.description}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-3 mt-4 text-xs text-[var(--text-secondary)]">
                  <span className="flex items-center space-x-1.5 bg-[var(--bg-elevated)] px-2.5 py-1 rounded-lg border border-[var(--bg-border)]">
                    <CalendarDays className="w-3.5 h-3.5 text-violet-400" />
                    <span>{formatDate(nextUpcomingTask.scheduled_date)}</span>
                  </span>
                  {nextUpcomingTask.start_time && (
                    <span className="flex items-center space-x-1.5 bg-[var(--bg-elevated)] px-2.5 py-1 rounded-lg border border-[var(--bg-border)]">
                      <Clock className="w-3.5 h-3.5 text-violet-400" />
                      <span>{formatTime(nextUpcomingTask.start_time)}</span>
                    </span>
                  )}
                  <span className="capitalize px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-400 font-medium">
                    {nextUpcomingTask.category}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center lg:text-left">
                <p className="text-base font-medium text-[var(--text-primary)]">All caught up!</p>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                  You have no pending tasks scheduled for today or upcoming days.
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--bg-border)] flex items-center justify-between">
            <span className="text-xs text-[var(--text-secondary)]">
              {nextUpcomingTask ? 'Scheduled in your plan' : 'Relax or plan ahead'}
            </span>
            <Link
              to="/tasks"
              className="inline-flex items-center space-x-1 text-xs font-semibold text-violet-500 hover:text-violet-400 transition-colors"
            >
              <span>View all tasks</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Today's Tasks Timeline Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold tracking-tight text-[var(--text-primary)]">
              Today&apos;s Schedule & Timeline
            </h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-500 border border-violet-500/20">
              {todayTasks.length} {todayTasks.length === 1 ? 'task' : 'tasks'}
            </span>
          </div>
          <Link
            to="/tasks"
            className="text-xs font-medium text-violet-500 hover:underline flex items-center space-x-1"
          >
            <span>Manage all</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)]">
            <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-2" />
            <p className="text-sm text-[var(--text-secondary)]">Loading tasks...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-center">
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
        ) : todayTasks.length === 0 ? (
          <div className="p-10 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-500/10 text-violet-500 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">No tasks scheduled for today</h3>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto">
              Your schedule is clear today. Click the button below to add your first task.
            </p>
            <button
              type="button"
              onClick={() => {
                setTaskToEdit(null);
                setIsTaskModalOpen(true);
              }}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium shadow-md shadow-violet-600/20 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Schedule Today</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {todayTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onComplete={handleCompleteTask}
                onReopen={handleReopenTask}
                onEdit={(t) => {
                  setTaskToEdit(t);
                  setIsTaskModalOpen(true);
                }}
                onReschedule={(t) => setTaskToReschedule(t)}
                onViewActivity={(t) => setTaskForActivity(t)}
                onDelete={(t) => setTaskToDelete(t)}
                isUpcomingHighlight={nextUpcomingTask?.id === task.id}
              />
            ))}
          </div>
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

      {/* Reschedule Modal */}
      <RescheduleModal
        isOpen={!!taskToReschedule}
        onClose={() => setTaskToReschedule(null)}
        task={taskToReschedule}
        onReschedule={handleReschedule}
      />

      {/* Task Activity Audit Modal */}
      <TaskActivityModal
        isOpen={!!taskForActivity}
        onClose={() => setTaskForActivity(null)}
        task={taskForActivity}
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
