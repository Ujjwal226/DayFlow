import React, { useEffect, useState, useCallback } from 'react';
import { activityLogsApi } from '../../api/activityLogs';
import { ActivityLog } from '../../types/activityLog';
import { ActivityItem } from './ActivityItem';
import { History, Loader2, AlertCircle } from 'lucide-react';

interface ActivityTimelineProps {
  taskId: string;
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ taskId }) => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchTimeline = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await activityLogsApi.getTaskActivityTimeline(taskId, page, 10);
      setLogs(data.items);
      setTotalPages(data.total_pages);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load task history.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [taskId, page]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin text-emerald-500 mr-2" />
        <span className="text-xs">Loading activity history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span>{error}</span>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center p-6 border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
        <History className="w-5 h-5 text-slate-500 mx-auto mb-2" />
        <p className="text-xs text-slate-400">No activity recorded for this task yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {logs.map((log) => (
          <ActivityItem key={log.id} activity={log} compact />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-400">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

