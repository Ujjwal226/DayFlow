import React from 'react';
import { Link } from 'react-router-dom';
import { Task } from '../../types/task';
import { TaskStatusBadge } from '../tasks/TaskStatusBadge';
import { TaskPriorityBadge } from '../tasks/TaskPriorityBadge';
import { Calendar, CheckCircle2, ChevronRight, Hash } from 'lucide-react';

interface OccurrenceListProps {
  occurrences: Task[];
  total: number;
  page: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  isLoading?: boolean;
}

export const OccurrenceList: React.FC<OccurrenceListProps> = ({
  occurrences,
  total,
  page,
  totalPages,
  onPageChange,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (occurrences.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-8 text-center">
        <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h4 className="text-sm font-semibold text-slate-300">No occurrences generated yet</h4>
        <p className="text-xs text-slate-500 mt-1">
          Occurrences are automatically generated as their scheduled target date arrives.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="divide-y divide-slate-800 rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        {occurrences.map((task) => (
          <div
            key={task.id}
            className="p-4 hover:bg-slate-900/80 transition flex items-center justify-between gap-4"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700/60 flex items-center justify-center text-xs font-bold text-slate-300 shrink-0">
                <Hash className="w-3 h-3 text-slate-500 mr-0.5" />
                {task.occurrence_index || '1'}
              </div>

              <div className="min-w-0">
                <Link
                  to={`/tasks/${task.id}`}
                  className="text-sm font-semibold text-white hover:text-emerald-400 transition flex items-center gap-1.5 truncate"
                >
                  <span className="truncate">{task.title}</span>
                </Link>
                <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>Occurrence Date: {task.occurrence_date || task.due_date?.substring(0, 10)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <TaskPriorityBadge priority={task.priority} />
              <TaskStatusBadge status={task.status} />
              <Link
                to={`/tasks/${task.id}`}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                title="View task details"
              >
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-400 px-2">
          <span>
            Showing page {page} of {totalPages} ({total} total occurrences)
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="px-3 py-1 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="px-3 py-1 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
