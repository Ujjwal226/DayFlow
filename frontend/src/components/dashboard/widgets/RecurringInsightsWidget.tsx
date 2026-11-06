import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { recurringTasksApi } from '../../../api/recurringTasks';
import { RecurringTask } from '../../../types/recurringTask';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { ArrowRight, Repeat } from 'lucide-react';
import { TaskListSkeleton } from '../WidgetSkeletons';

export const RecurringInsightsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [recurringTasks, setRecurringTasks] = useState<RecurringTask[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecurring = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await recurringTasksApi.list({ is_active: true });
      setRecurringTasks(res.items.slice(0, 5));
    } catch {
      setError('Unable to load recurring tasks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecurring();
  }, []);

  return (
    <WidgetContainer
      title="Recurring Tasks"
      description="Active series and upcoming runs"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<TaskListSkeleton />}
      error={error}
      onRetry={fetchRecurring}
      headerAction={
        <Link
          to="/recurring-tasks"
          className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 font-medium transition"
        >
          <span>Manage</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {recurringTasks.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <Repeat className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-medium text-slate-400">No active recurring tasks</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Automate daily, weekly, or monthly routines</p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-64 pr-1">
          {recurringTasks.map((series) => (
            <div
              key={series.id}
              className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-950 transition group"
            >
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <Repeat className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                <div className="min-w-0">
                  <span className="text-xs text-slate-200 group-hover:text-purple-300 transition truncate font-medium block">
                    {series.title}
                  </span>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                    <span className="capitalize">{series.frequency.toLowerCase()}</span>
                    {series.next_occurrence_date && (
                      <span className="flex items-center gap-1">
                        &bull; Next: {series.next_occurrence_date}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 shrink-0">
                Active
              </span>
            </div>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};
