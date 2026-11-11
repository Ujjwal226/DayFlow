import React from 'react';
import { Target, CheckCircle2, Clock, AlertTriangle, Calendar, ChevronRight, Edit3, Trash2, Check } from 'lucide-react';
import { Goal, GoalPriority, GoalStatus } from '../../types/goal';

interface GoalCardProps {
  goal: Goal;
  onSelect: (goal: Goal) => void;
  onEdit: (goal: Goal) => void;
  onDelete: (goalId: string) => void;
  onToggleComplete: (goal: Goal) => void;
}

const PRIORITY_BADGES: Record<GoalPriority, { label: string; className: string }> = {
  LOW: { label: 'Low', className: 'bg-slate-800 text-slate-300 border-slate-700' },
  MEDIUM: { label: 'Medium', className: 'bg-blue-900/40 text-blue-300 border-blue-800/60' },
  HIGH: { label: 'High', className: 'bg-amber-900/40 text-amber-300 border-amber-800/60' },
  URGENT: { label: 'Urgent', className: 'bg-rose-900/40 text-rose-300 border-rose-800/60' },
};

const STATUS_BADGES: Record<GoalStatus, { label: string; className: string; icon: React.ReactNode }> = {
  NOT_STARTED: {
    label: 'Not Started',
    className: 'bg-slate-800/60 text-slate-400 border-slate-700',
    icon: <Clock className="w-3 h-3" />,
  },
  IN_PROGRESS: {
    label: 'In Progress',
    className: 'bg-indigo-950/60 text-indigo-300 border-indigo-800/60',
    icon: <Clock className="w-3 h-3 text-indigo-400" />,
  },
  ON_TRACK: {
    label: 'On Track',
    className: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60',
    icon: <CheckCircle2 className="w-3 h-3 text-emerald-400" />,
  },
  AT_RISK: {
    label: 'At Risk',
    className: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
    icon: <AlertTriangle className="w-3 h-3 text-rose-400" />,
  },
  COMPLETED: {
    label: 'Completed',
    className: 'bg-teal-950/60 text-teal-300 border-teal-800/60',
    icon: <Check className="w-3 h-3 text-teal-400" />,
  },
  CANCELLED: {
    label: 'Cancelled',
    className: 'bg-zinc-800 text-zinc-400 border-zinc-700',
    icon: <AlertTriangle className="w-3 h-3 text-zinc-400" />,
  },
};

export const GoalCard: React.FC<GoalCardProps> = ({
  goal,
  onSelect,
  onEdit,
  onDelete,
  onToggleComplete,
}) => {
  const isCompleted = goal.status === 'COMPLETED';
  const progressPercent = Math.min(100, Math.max(0, Math.round(goal.progress_percentage || 0)));
  const completedMilestones = goal.completed_milestone_count ?? (goal.milestones ? goal.milestones.filter((m) => m.is_completed).length : 0);
  const totalMilestones = goal.milestone_count ?? (goal.milestones ? goal.milestones.length : 0);

  const priorityBadge = PRIORITY_BADGES[goal.priority] || PRIORITY_BADGES.MEDIUM;
  const statusBadge = STATUS_BADGES[goal.status] || STATUS_BADGES.IN_PROGRESS;

  const isOverdue =
    goal.target_date &&
    !isCompleted &&
    new Date(goal.target_date).setHours(23, 59, 59, 999) < Date.now();

  return (
    <div
      role="article"
      data-testid={`goal-card-${goal.id}`}
      onClick={() => onSelect(goal)}
      className="group relative bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
    >
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge.className}`}
            >
              {statusBadge.icon}
              {statusBadge.label}
            </span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${priorityBadge.className}`}
            >
              {priorityBadge.label}
            </span>
            <span className="text-xs text-slate-400 bg-slate-800/40 px-2 py-0.5 rounded border border-slate-700/50 capitalize">
              {goal.category.toLowerCase()}
            </span>
          </div>

          {/* Quick Actions (Prevent bubbling) */}
          <div
            className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => onToggleComplete(goal)}
              title={isCompleted ? 'Reopen Goal' : 'Mark Completed'}
              aria-label={isCompleted ? 'Reopen Goal' : 'Mark Completed'}
              className={`p-1.5 rounded-lg border text-xs transition ${
                isCompleted
                  ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300 hover:bg-emerald-900'
                  : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:text-emerald-300 hover:border-emerald-600'
              }`}
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => onEdit(goal)}
              title="Edit Goal"
              aria-label="Edit Goal"
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-400 hover:text-white hover:border-slate-600 transition text-xs"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => onDelete(goal.id)}
              title="Delete Goal"
              aria-label="Delete Goal"
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-400 hover:text-rose-400 hover:border-rose-800 transition text-xs"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Title & Description */}
        <div className="mb-4">
          <h3
            className={`font-semibold text-base line-clamp-1 ${
              isCompleted ? 'text-slate-400 line-through' : 'text-white group-hover:text-indigo-300'
            } transition`}
          >
            {goal.title}
          </h3>
          {goal.description && (
            <p className="text-slate-400 text-xs mt-1 line-clamp-2 leading-relaxed">
              {goal.description}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="text-slate-400 flex items-center gap-1 font-medium">
              <Target className="w-3 h-3 text-indigo-400" />
              Progress ({goal.progress_method})
            </span>
            <span className="font-semibold text-slate-200">{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/40">
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                isCompleted
                  ? 'bg-teal-500'
                  : progressPercent >= 75
                  ? 'bg-emerald-500'
                  : progressPercent >= 35
                  ? 'bg-indigo-500'
                  : 'bg-amber-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          {goal.progress_method === 'NUMERIC' && goal.target_value && (
            <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
              <span>Current: {goal.current_value || 0}</span>
              <span>Target: {goal.target_value} {goal.unit || ''}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-3">
          {goal.target_date && (
            <span
              className={`flex items-center gap-1 ${
                isOverdue ? 'text-rose-400 font-medium' : 'text-slate-400'
              }`}
            >
              <Calendar className="w-3 h-3" />
              {new Date(goal.target_date).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
              })}
            </span>
          )}

          {totalMilestones > 0 && (
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-slate-500" />
              {completedMilestones}/{totalMilestones} milestones
            </span>
          )}

          {goal.linked_task_count > 0 && (
            <span className="text-slate-500">
              {goal.linked_task_count} task{goal.linked_task_count === 1 ? '' : 's'}
            </span>
          )}
        </div>

        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition" />
      </div>
    </div>
  );
};
