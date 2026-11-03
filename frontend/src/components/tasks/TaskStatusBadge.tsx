import React from 'react';
import { TaskStatus } from '../../types/task';
import { CheckCircle2, Clock, CircleDot, XCircle } from 'lucide-react';

interface TaskStatusBadgeProps {
  status: TaskStatus;
  className?: string;
}

export const TaskStatusBadge: React.FC<TaskStatusBadgeProps> = ({ status, className = '' }) => {
  switch (status) {
    case 'COMPLETED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 ${className}`}
        >
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Completed
        </span>
      );
    case 'IN_PROGRESS':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30 ${className}`}
        >
          <Clock className="w-3 h-3 text-sky-400" />
          In Progress
        </span>
      );
    case 'CANCELLED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700 ${className}`}
        >
          <XCircle className="w-3 h-3 text-slate-400" />
          Cancelled
        </span>
      );
    case 'TODO':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700 ${className}`}
        >
          <CircleDot className="w-3 h-3 text-slate-400" />
          Todo
        </span>
      );
  }
};

