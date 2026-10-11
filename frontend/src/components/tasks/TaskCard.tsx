import React from 'react';
import {
  Check,
  Clock,
  Calendar,
  Pencil,
  Trash2,
  AlertCircle,
  RotateCcw,
  CalendarClock,
  History,
  Sparkles,
} from 'lucide-react';
import type { Task } from '../../types/api';
import { PriorityBadge, CategoryBadge } from '../common/Badge';
import { formatDate, formatTime, isOverdue } from '../../lib/utils';
import { cn } from '../../lib/utils';

interface TaskCardProps {
  task: Task;
  onComplete: (id: number) => void;
  onReopen?: (id: number) => void;
  onEdit: (task: Task) => void;
  onReschedule?: (task: Task) => void;
  onViewActivity?: (task: Task) => void;
  onDelete: (task: Task) => void;
  isUpcomingHighlight?: boolean;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onComplete,
  onReopen,
  onEdit,
  onReschedule,
  onViewActivity,
  onDelete,
  isUpcomingHighlight = false,
}) => {
  const completed = task.status === 'completed';
  const overdue = isOverdue(task.scheduled_date, task.status);
  const isRescheduled =
    task.original_scheduled_date &&
    task.original_scheduled_date !== task.scheduled_date;

  return (
    <div
      className={cn(
        'group relative flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 sm:p-5 rounded-2xl border transition-all duration-200 gap-4',
        'bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)]',
        completed
          ? 'opacity-75 border-[var(--bg-border)]/60 bg-[var(--bg-elevated)]/40'
          : overdue
          ? 'border-rose-500/40 bg-rose-500/[0.03] shadow-sm'
          : isUpcomingHighlight
          ? 'border-violet-500/50 bg-violet-500/[0.04] ring-1 ring-violet-500/30 shadow-md'
          : 'border-[var(--bg-border)] hover:border-violet-500/30 hover:shadow-md'
      )}
    >
      {/* Left side: Checkbox + Details */}
      <div className="flex items-start space-x-3.5 flex-1 min-w-0">
        {/* Checkbox (Complete / Reopen toggle) */}
        <button
          type="button"
          onClick={() => {
            if (completed) {
              if (onReopen) onReopen(task.id);
            } else {
              onComplete(task.id);
            }
          }}
          className={cn(
            'w-6 h-6 rounded-lg flex items-center justify-center border mt-0.5 transition-all duration-200 shrink-0 focus:outline-none focus:ring-2 focus:ring-violet-500',
            completed
              ? 'bg-emerald-500 border-emerald-500 text-white hover:bg-emerald-600 cursor-pointer'
              : 'border-[var(--text-secondary)]/50 hover:border-violet-500 hover:bg-violet-500/10 cursor-pointer'
          )}
          title={completed ? 'Click to reopen task' : `Mark "${task.title}" as complete`}
          aria-label={completed ? `Reopen task "${task.title}"` : `Mark "${task.title}" as complete`}
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

            {/* Next Upcoming Highlight Tag */}
            {isUpcomingHighlight && !completed && (
              <span className="inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-md bg-violet-500/15 text-violet-400 border border-violet-500/30">
                <Sparkles className="w-3 h-3 mr-1 text-violet-400" /> Next Up
              </span>
            )}

            {/* Overdue alert */}
            {overdue && (
              <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-500 border border-rose-500/20">
                <AlertCircle className="w-3 h-3 mr-1" /> Overdue
              </span>
            )}

            {/* Rescheduled badge */}
            {isRescheduled && (
              <span
                className="inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20"
                title={`Originally scheduled for ${task.original_scheduled_date}`}
              >
                <CalendarClock className="w-3 h-3 mr-1" /> Rescheduled
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

            {/* Scheduled Date */}
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
      <div className="flex items-center space-x-1 sm:opacity-90 group-hover:opacity-100 transition-opacity self-end sm:self-center shrink-0">
        {/* Reopen Action (when completed) */}
        {completed && onReopen && (
          <button
            type="button"
            onClick={() => onReopen(task.id)}
            className="p-2 rounded-lg text-amber-400 hover:text-amber-300 hover:bg-amber-400/10 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
            title="Reopen task"
            aria-label={`Reopen task ${task.title}`}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}

        {/* Reschedule Action */}
        {onReschedule && !completed && (
          <button
            type="button"
            onClick={() => onReschedule(task)}
            className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-violet-400 hover:bg-violet-400/10 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500"
            title="Reschedule task"
            aria-label={`Reschedule task ${task.title}`}
          >
            <CalendarClock className="w-4 h-4" />
          </button>
        )}

        {/* Activity Log */}
        {onViewActivity && (
          <button
            type="button"
            onClick={() => onViewActivity(task)}
            className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500"
            title="View activity history"
            aria-label={`View activity history for ${task.title}`}
          >
            <History className="w-4 h-4" />
          </button>
        )}

        {/* Edit Action */}
        <button
          type="button"
          onClick={() => onEdit(task)}
          className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500"
          title="Edit task"
          aria-label={`Edit task ${task.title}`}
        >
          <Pencil className="w-4 h-4" />
        </button>

        {/* Delete Action */}
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
