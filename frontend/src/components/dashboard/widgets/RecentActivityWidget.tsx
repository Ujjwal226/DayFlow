import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { activityLogsApi } from '../../../api/activityLogs';
import { ActivityLog } from '../../../types/activityLog';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { ActivityItem } from '../../activity/ActivityItem';
import { ArrowRight, History } from 'lucide-react';
import { ActivityFeedSkeleton } from '../WidgetSkeletons';

export const RecentActivityWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await activityLogsApi.getGlobalActivities({ page: 1, page_size: 5 });
      setActivities(res.items);
    } catch {
      setError('Unable to load recent activity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  return (
    <WidgetContainer
      title="Recent Activity"
      description="Latest actions across your workspace"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<ActivityFeedSkeleton />}
      error={error}
      onRetry={fetchActivities}
      headerAction={
        <Link
          to="/activity"
          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
        >
          <span>Activity Log</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {activities.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <History className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-medium text-slate-400">No recent activity recorded</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Actions like task completions will appear here</p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-64 pr-1">
          {activities.map((act) => (
            <ActivityItem key={act.id} activity={act} compact />
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};

