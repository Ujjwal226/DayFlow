import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../../api/goals';
import { GoalResponse } from '../../../types/goal';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';

export const RecentlyCompletedGoalsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [completions, setCompletions] = useState<GoalResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCompletions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.getAnalytics();
      setCompletions(res.recent_completions || []);
    } catch {
      setError('Unable to load recently completed goals.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompletions();
  }, []);

  return (
    <WidgetContainer
      title="Recently Completed"
      description="Accomplished goals"
      size={widgetConfig.size}
      isLoading={loading}
      error={error}
      onRetry={fetchCompletions}
      headerAction={
        <Link
          to="/goals"
          className="inline-flex items-center gap-1 text-xs text-teal-400 hover:text-teal-300 font-medium transition"
        >
          <span>History</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {completions.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
          No completed goals yet. Keep going!
        </p>
      ) : (
        <div className="space-y-2">
          {completions.slice(0, 4).map((goal) => (
            <div
              key={goal.id}
              className="flex items-center justify-between p-2 rounded-lg bg-teal-50/40 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/40 text-xs"
            >
              <span className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[190px]">
                {goal.title}
              </span>
              <span className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold">
                100%
              </span>
            </div>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};
