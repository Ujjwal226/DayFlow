import React from 'react';
import { TaskPriority } from '../../types/task';
import { ArrowDown, ArrowUp, Flame } from 'lucide-react';

interface TaskPriorityBadgeProps {
  priority: TaskPriority;
  className?: string;
}

export const TaskPriorityBadge: React.FC<TaskPriorityBadgeProps> = ({ priority, className = '' }) => {
  switch (priority) {
    case 'URGENT':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30 ${className}`}
        >
          <Flame className="w-3 h-3 text-rose-400" />
          Urgent
        </span>
      );
    case 'HIGH':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 ${className}`}
        >
          <ArrowUp className="w-3 h-3 text-amber-400" />
          High
        </span>
      );
    case 'MEDIUM':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 ${className}`}
        >
          Medium
        </span>
      );
    case 'LOW':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700 ${className}`}
        >
          <ArrowDown className="w-3 h-3 text-slate-400" />
          Low
        </span>
      );
  }
};
