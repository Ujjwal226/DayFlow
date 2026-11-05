import React from 'react';
import { ActivityLog } from '../../types/activityLog';
import { ActivityItem } from './ActivityItem';
import { History, Loader2, AlertCircle } from 'lucide-react';

interface ActivityFeedProps {
  logs: ActivityLog[];
  isLoading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  logs,
  isLoading,
  error,
  page,
  totalPages,
  onPageChange,
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500 mb-3" />
        <p className="text-sm">Loading activity feed...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <p>{error}</p>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-500 mb-3">
          <History className="w-6 h-6" />
        </div>
        <h3 className="text-base font-medium text-slate-200">No activity recorded yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Actions such as creating tasks, completing subtasks, or scheduling recurring tasks will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2.5">
        {logs.map((log) => (
          <ActivityItem key={log.id} activity={log} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs text-slate-400">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

