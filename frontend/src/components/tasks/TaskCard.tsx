import React from 'react';
import { Task } from '../../types/task';
import { TaskPriorityBadge } from './TaskPriorityBadge';
import { TaskStatusBadge } from './TaskStatusBadge';
import {
  Calendar,
  AlertTriangle,
  Copy,
  Archive,
  ArchiveRestore,
  Trash2,
  Edit2,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDuplicate: (taskId: string) => void;
  onArchiveToggle: (taskId: string, isArchived: boolean) => void;
  onDelete: (taskId: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onEdit,
  onDuplicate,
  onArchiveToggle,
  onDelete,
}) => {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div
      className={`group relative rounded-2xl border p-5 transition-all duration-200 ${
        task.is_archived
          ? 'bg-slate-900/30 border-slate-800/60 opacity-70 hover:opacity-100'
          : task.is_overdue
          ? 'bg-rose-950/10 border-rose-500/30 hover:border-rose-500/50 shadow-lg shadow-rose-950/10'
          : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900 shadow-md'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <TaskStatusBadge status={task.status} />
            <TaskPriorityBadge priority={task.priority} />
            {task.is_overdue && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                <AlertTriangle className="w-3 h-3 text-rose-400" />
                Overdue
              </span>
            )}
            {task.is_archived && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                Archived
              </span>
            )}
          </div>

          <Link
            to={`/tasks/${task.id}`}
            className="block group-hover:text-emerald-400 transition"
          >
            <h3
              className={`text-base font-semibold text-white tracking-tight break-words ${
                task.status === 'COMPLETED' ? 'line-through text-slate-400' : ''
              }`}
            >
              {task.title}
            </h3>
          </Link>

          {task.description && (
            <p className="mt-1.5 text-xs text-slate-400 line-clamp-2 leading-relaxed break-words">
              {task.description}
            </p>
          )}
        </div>

        {/* Quick Actions Dropdown / Bar */}
        <div className="flex items-center gap-1 shrink-0 opacity-80 group-hover:opacity-100 transition">
          <button
            onClick={() => onEdit(task)}
            title="Edit task"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDuplicate(task.id)}
            title="Duplicate task"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={() => onArchiveToggle(task.id, task.is_archived)}
            title={task.is_archived ? 'Restore task' : 'Archive task'}
            className="p-1.5 rounded-lg text-slate-400 hover:text-amber-300 hover:bg-amber-500/10 transition"
          >
            {task.is_archived ? (
              <ArchiveRestore className="w-4 h-4" />
            ) : (
              <Archive className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={() => onDelete(task.id)}
            title="Delete task"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Footer details: Due date and link */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-3">
          {task.due_date ? (
            <div
              className={`flex items-center gap-1.5 ${
                task.is_overdue ? 'text-rose-400 font-medium' : 'text-slate-400'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Due {formatDate(task.due_date)}</span>
            </div>
          ) : (
            <span className="text-slate-500">No deadline</span>
          )}
        </div>

        <Link
          to={`/tasks/${task.id}`}
          className="inline-flex items-center gap-1 text-slate-400 hover:text-emerald-400 transition"
        >
          <span>Details</span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
};

