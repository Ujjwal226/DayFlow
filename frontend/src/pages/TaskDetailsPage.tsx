import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { tasksApi } from '../api/tasks';
import { Task, TaskCreatePayload } from '../types/task';
import { TaskPriorityBadge } from '../components/tasks/TaskPriorityBadge';
import { TaskStatusBadge } from '../components/tasks/TaskStatusBadge';
import { TaskFormModal } from '../components/tasks/TaskForm';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Copy,
  Archive,
  ArchiveRestore,
  Trash2,
  Edit2,
  AlertTriangle,
  Loader2,
  CheckCircle2,
} from 'lucide-react';

export const TaskDetailsPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchTask = React.useCallback(async () => {
    if (!taskId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await tasksApi.getTask(taskId);
      setTask(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Task not found.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  const handleUpdate = async (payload: TaskCreatePayload) => {
    if (!task) return;
    const updated = await tasksApi.updateTask(task.id, payload);
    setTask(updated);
  };

  const handleDuplicate = async () => {
    if (!task) return;
    const dup = await tasksApi.duplicateTask(task.id);
    navigate(`/tasks/${dup.id}`);
  };

  const handleArchiveToggle = async () => {
    if (!task) return;
    if (task.is_archived) {
      const restored = await tasksApi.restoreTask(task.id);
      setTask(restored);
    } else {
      const archived = await tasksApi.archiveTask(task.id);
      setTask(archived);
    }
  };

  const handleDelete = async () => {
    if (!task) return;
    setIsDeleting(true);
    try {
      await tasksApi.deleteTask(task.id);
      navigate('/tasks');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete task.';
      setError(msg);
      setIsDeleting(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Not set';
    return new Date(dateStr).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center text-slate-100">
        <div className="p-4 rounded-3xl bg-rose-500/10 border border-rose-500/20 text-rose-300 max-w-md w-full">
          <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
          <h2 className="text-base font-bold text-white mb-1">Unable to Load Task</h2>
          <p className="text-xs text-rose-300/80 mb-4">{error || 'Task not found or access restricted.'}</p>
          <Link
            to="/tasks"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Tasks</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            to="/tasks"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-xs font-medium transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Tasks</span>
          </Link>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>
            <button
              onClick={handleDuplicate}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Duplicate</span>
            </button>
            <button
              onClick={handleArchiveToggle}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
            >
              {task.is_archived ? <ArchiveRestore className="w-3.5 h-3.5" /> : <Archive className="w-3.5 h-3.5" />}
              <span>{task.is_archived ? 'Restore' : 'Archive'}</span>
            </button>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-medium border border-rose-500/30 transition flex items-center gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Task View */}
      <main className="max-w-4xl mx-auto px-6 py-10 flex-1 w-full">
        <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
          {/* Header Badges */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <TaskStatusBadge status={task.status} />
            <TaskPriorityBadge priority={task.priority} />
            {task.is_overdue && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                <AlertTriangle className="w-3 h-3 text-rose-400" />
                Overdue
              </span>
            )}
            {task.is_archived && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                Archived
              </span>
            )}
          </div>

          {/* Title */}
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight break-words">
            {task.title}
          </h1>

          {/* Description */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Description
            </h3>
            {task.description ? (
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
                {task.description}
              </p>
            ) : (
              <p className="text-xs text-slate-500 italic">No description provided.</p>
            )}
          </div>

          {/* Scheduling & Lifecycle Meta */}
          <div className="mt-8 pt-6 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div className="p-3.5 rounded-2xl bg-slate-800/40 border border-slate-800">
              <span className="text-slate-500 block mb-1">Start Date</span>
              <span className="text-slate-300 font-medium flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {formatDate(task.start_date)}
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/40 border border-slate-800">
              <span className="text-slate-500 block mb-1">Due Date</span>
              <span
                className={`font-medium flex items-center gap-1.5 ${
                  task.is_overdue ? 'text-rose-400 font-bold' : 'text-slate-300'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                {formatDate(task.due_date)}
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/40 border border-slate-800">
              <span className="text-slate-500 block mb-1">Completed At</span>
              <span className="text-slate-300 font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                {formatDate(task.completed_at)}
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/40 border border-slate-800">
              <span className="text-slate-500 block mb-1">Created At</span>
              <span className="text-slate-300 font-medium">{formatDate(task.created_at)}</span>
            </div>
          </div>
        </div>
      </main>

      {/* Edit Modal */}
      <TaskFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleUpdate}
        initialTask={task}
      />
    </div>
  );
};
