import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../../api/goals';
import { GoalResponse } from '../../../types/goal';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';

export const UpcomingGoalDeadlinesWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [deadlines, setDeadlines] = useState<GoalResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDeadlines = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.getAnalytics();
      setDeadlines(res.upcoming_deadlines || []);
    } catch {
      setError('Unable to load upcoming deadlines.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeadlines();
  }, []);

  return (
    <WidgetContainer
      title="Goal Deadlines"
      description="Approaching goal deadlines"
      size={widgetConfig.size}
      isLoading={loading}
      error={error}
      onRetry={fetchDeadlines}
      headerAction={
        <Link
          to="/goals"
          className="inline-flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 font-medium transition"
        >
          <span>Planning</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {deadlines.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
          No upcoming goal deadlines within the horizon.
        </p>
      ) : (
        <div className="space-y-2.5">
          {deadlines.slice(0, 4).map((goal) => (
            <div
              key={goal.id}
              className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-800"
            >
              <div className="truncate max-w-[170px]">
                <p className="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">
                  {goal.title}
                </p>
                <p className="text-[11px] text-gray-500 dark:text-gray-400">
                  {goal.target_date || 'No date'}
                </p>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                {goal.progress_percentage}%
              </span>
            </div>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};
