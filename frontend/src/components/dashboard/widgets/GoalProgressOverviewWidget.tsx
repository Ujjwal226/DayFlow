import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../../api/goals';
import { GoalAnalyticsOverview } from '../../../types/goal';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';

export const GoalProgressOverviewWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [analytics, setAnalytics] = useState<GoalAnalyticsOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.getAnalytics();
      setAnalytics(res);
    } catch {
      setError('Unable to load goal progress metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <WidgetContainer
      title="Goal Progress"
      description="Completion & progress rates"
      size={widgetConfig.size}
      isLoading={loading}
      error={error}
      onRetry={fetchAnalytics}
      headerAction={
        <Link
          to="/goals"
          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
        >
          <span>Analytics</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="p-2.5 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
            <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
              {analytics?.completion_rate ?? 0}%
            </p>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">Completion Rate</p>
          </div>
          <div className="p-2.5 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30">
            <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
              {analytics?.average_progress_percentage ?? 0}%
            </p>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">Avg Progress</p>
          </div>
        </div>

        <div className="flex justify-between items-center text-xs text-gray-600 dark:text-gray-300 px-1 pt-1">
          <span>Active Goals: <strong>{analytics?.active_goals ?? 0}</strong></span>
          <span>Completed: <strong>{analytics?.completed_goals ?? 0}</strong></span>
        </div>
      </div>
    </WidgetContainer>
  );
};
