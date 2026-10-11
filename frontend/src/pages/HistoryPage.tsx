import React, { useState, useEffect } from 'react';
import { History, CheckCircle2, Clock, Sparkles, Loader2, Calendar } from 'lucide-react';
import { tasksApi } from '../lib/api';
import type { Task } from '../types/api';
import { PriorityBadge, CategoryBadge } from '../components/common/Badge';
import { formatDate } from '../lib/utils';
import { Link } from 'react-router-dom';

export const HistoryPage: React.FC = () => {
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await tasksApi.list({ status: 'completed', limit: 50 });
        setCompletedTasks(res.tasks);
      } catch {
        // Fallback gracefully
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 text-violet-500 font-medium text-xs tracking-wider uppercase mb-1">
          <History className="w-4 h-4" />
          <span>Stage 2 Preview</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
          Task History
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          A dedicated archive of your accomplishments and productivity records.
        </p>
      </div>

      {/* Stage 3 Feature Spotlight Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-violet-950/30 via-[var(--bg-surface)] to-[var(--bg-surface)] border border-violet-500/20 shadow-sm relative overflow-hidden">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 rounded-xl bg-violet-600/20 text-violet-400 flex items-center justify-center shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-400 uppercase tracking-wider">
              Coming in Stage 3
            </span>
            <h2 className="text-lg font-bold text-[var(--text-primary)] mt-2">
              Deep Productivity Analytics & History Timeline
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1 leading-relaxed max-w-2xl">
              Stage 3 will introduce comprehensive audit events (`TaskEvent`), rollover tracking for rescheduled tasks, weekly velocity charts, and focus streak statistics.
            </p>
          </div>
        </div>
      </div>

      {/* Real Completed Tasks Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold tracking-tight text-[var(--text-primary)]">
            Completed Tasks Archive
          </h2>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
            {completedTasks.length} Completed
          </span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)]">
            <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-2" />
            <p className="text-sm text-[var(--text-secondary)]">Loading archive...</p>
          </div>
        ) : completedTasks.length === 0 ? (
          <div className="p-10 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">No completed tasks yet</h3>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mx-auto">
              Once you mark tasks as completed on your Dashboard or My Tasks page, they will be archived here.
            </p>
            <Link
              to="/tasks"
              className="inline-flex items-center px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium transition-colors"
            >
              Go to My Tasks
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {completedTasks.map((task) => (
              <div
                key={task.id}
                className="p-4 sm:p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] flex flex-col sm:flex-row sm:items-center justify-between gap-3 opacity-80 hover:opacity-100 transition-opacity"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-500 flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="text-base font-medium text-[var(--text-primary)] line-through">
                      {task.title}
                    </h3>
                    {task.description && (
                      <p className="text-sm text-[var(--text-secondary)] mt-0.5 line-clamp-1">
                        {task.description}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-[var(--text-secondary)]">
                      <PriorityBadge priority={task.priority} />
                      <CategoryBadge category={task.category} />
                      <span className="flex items-center space-x-1 pl-1">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Scheduled: {formatDate(task.scheduled_date)}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {task.completed_at && (
                  <div className="text-xs text-[var(--text-secondary)] flex items-center space-x-1 self-end sm:self-center bg-[var(--bg-elevated)] px-2.5 py-1 rounded-lg">
                    <Clock className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Completed {new Date(task.completed_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
