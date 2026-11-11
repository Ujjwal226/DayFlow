import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../../api/goals';
import { GoalResponse } from '../../../types/goal';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';

export const AtRiskGoalsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [atRiskGoals, setAtRiskGoals] = useState<GoalResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAtRisk = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.listGoals({ status: 'AT_RISK', is_archived: false, page_size: 5 });
      setAtRiskGoals(res.items || []);
    } catch {
      setError('Unable to load at-risk goals.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAtRisk();
  }, []);

  return (
    <WidgetContainer
      title="At-Risk Goals"
      description="Goals requiring attention"
      size={widgetConfig.size}
      isLoading={loading}
      error={error}
      onRetry={fetchAtRisk}
      headerAction={
        <Link
          to="/goals"
          className="inline-flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 font-medium transition"
        >
          <span>Review</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {atRiskGoals.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
          Great work! No goals are currently marked at risk.
        </p>
      ) : (
        <div className="space-y-2">
          {atRiskGoals.slice(0, 4).map((goal) => (
            <div
              key={goal.id}
              className="flex items-center justify-between p-2 rounded-lg bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-xs"
            >
              <div className="truncate max-w-[170px]">
                <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                  {goal.title}
                </p>
                <p className="text-[11px] text-rose-500">
                  {goal.target_date ? `Due ${goal.target_date}` : 'Needs attention'}
                </p>
              </div>
              <span className="font-bold text-rose-600 dark:text-rose-400">
                {goal.progress_percentage}%
              </span>
            </div>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};
