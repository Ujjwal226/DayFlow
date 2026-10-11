import React from 'react';
import { Check, Clock, Calendar, Pencil, Trash2, AlertCircle } from 'lucide-react';
import type { Task } from '../../types/api';
import { PriorityBadge, CategoryBadge } from '../common/Badge';
import { formatDate, formatTime, isOverdue } from '../../lib/utils';
import { cn } from '../../lib/utils';

interface TaskCardProps {
  task: Task;
  onComplete: (id: number) => void;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onComplete,
  onEdit,
  onDelete,
}) => {
  const completed = task.status === 'completed';
  const overdue = isOverdue(task.scheduled_date, task.status);

  return (
    <div
      className={cn(
        'group relative flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 sm:p-5 rounded-2xl border transition-all duration-200 gap-4',
        'bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)]',
        completed
          ? 'opacity-70 border-[var(--bg-border)]/60'
          : overdue
          ? 'border-rose-500/40 bg-rose-500/[0.02]'
          : 'border-[var(--bg-border)] hover:border-violet-500/30 hover:shadow-md'
      )}
    >
      {/* Left side: Checkbox + Details */}
      <div className="flex items-start space-x-3.5 flex-1 min-w-0">
        {/* Complete Checkbox */}
        <button
          type="button"
          onClick={() => {
            if (!completed) onComplete(task.id);
          }}
          disabled={completed}
          className={cn(
            'w-6 h-6 rounded-lg flex items-center justify-center border mt-0.5 transition-all duration-200 shrink-0 focus:outline-none focus:ring-2 focus:ring-violet-500',
            completed
              ? 'bg-emerald-500 border-emerald-500 text-white cursor-default'
              : 'border-[var(--text-secondary)]/50 hover:border-violet-500 hover:bg-violet-500/10 cursor-pointer'
          )}
          aria-label={completed ? 'Task completed' : `Mark "${task.title}" as complete`}
        >
          {completed && <Check className="w-3.5 h-3.5 stroke-[3]" />}
        </button>

        {/* Task Title & Content */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3
              className={cn(
                'text-base font-medium tracking-tight text-[var(--text-primary)] transition-all',
                completed && 'line-through text-[var(--text-secondary)]'
              )}
            >
              {task.title}
            </h3>

            {/* Overdue alert */}
            {overdue && (
              <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-500 border border-rose-500/20">
                <AlertCircle className="w-3 h-3 mr-1" /> Overdue
              </span>
            )}
          </div>

          {task.description && (
            <p className="text-sm text-[var(--text-secondary)] line-clamp-2 mb-2 font-normal leading-relaxed">
              {task.description}
            </p>
          )}

          {/* Meta row: Badges, Date, Time */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)]">
            <PriorityBadge priority={task.priority} />
            <CategoryBadge category={task.category} />

            {/* Date */}
            <div className="flex items-center space-x-1 pl-1">
              <Calendar className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
              <span>{formatDate(task.scheduled_date)}</span>
            </div>

            {/* Time range if present */}
            {(task.start_time || task.end_time) && (
              <div className="flex items-center space-x-1 border-l border-[var(--bg-border)] pl-2">
                <Clock className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                <span>
                  {task.start_time ? formatTime(task.start_time) : ''}
                  {task.start_time && task.end_time ? ' - ' : ''}
                  {task.end_time ? formatTime(task.end_time) : ''}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right side: Action buttons */}
      <div className="flex items-center space-x-1 sm:opacity-0 group-hover:opacity-100 transition-opacity self-end sm:self-center shrink-0">
        <button
          type="button"
          onClick={() => onEdit(task)}
          className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500"
          title="Edit task"
          aria-label={`Edit task ${task.title}`}
        >
          <Pencil className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={() => onDelete(task)}
          className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-rose-500 hover:bg-rose-500/10 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
          title="Delete task"
          aria-label={`Delete task ${task.title}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
