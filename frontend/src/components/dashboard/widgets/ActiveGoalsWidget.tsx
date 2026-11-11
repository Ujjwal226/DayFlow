import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../../api/goals';
import { GoalResponse } from '../../../types/goal';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';

export const ActiveGoalsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGoals = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.listGoals({ is_archived: false, page_size: 10 });
      const active = (res.items || []).filter(g => g.status !== 'COMPLETED' && g.status !== 'CANCELLED');
      setGoals(active);
    } catch {
      setError('Unable to load active goals.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  return (
    <WidgetContainer
      title="Active Goals"
      description="Ongoing goals and current progress"
      size={widgetConfig.size}
      isLoading={loading}
      error={error}
      onRetry={fetchGoals}
      headerAction={
        <Link
          to="/goals"
          className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition"
        >
          <span>Goals</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {goals.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
          No active goals found. Start by setting a new goal!
        </p>
      ) : (
        <div className="space-y-3">
          {goals.slice(0, 4).map((goal) => (
            <div key={goal.id} className="border border-gray-100 dark:border-gray-800 rounded-lg p-2.5">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[180px]">
                  {goal.title}
                </span>
                <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                  {goal.progress_percentage}%
                </span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 dark:bg-indigo-500 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, goal.progress_percentage)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};
