import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../../api/analytics';
import { ProductivityOverviewResponse } from '../../../types/analytics';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { ArrowRight, CheckCircle2, Clock, AlertCircle, TrendingUp } from 'lucide-react';
import { KpiGridSkeleton } from '../WidgetSkeletons';

export const ProductivityOverviewWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [overview, setOverview] = useState<ProductivityOverviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.getOverview({ days: 30 });
      setOverview(res);
    } catch {
      setError('Unable to load productivity overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  return (
    <WidgetContainer
      title="Productivity Overview"
      description="Trailing 30-day performance KPIs"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<KpiGridSkeleton />}
      error={error}
      onRetry={fetchOverview}
      headerAction={
        <Link
          to="/analytics"
          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
        >
          <span>Analytics</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-400 font-medium">Completion Rate</span>
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {overview ? `${overview.completion_rate.toFixed(1)}%` : '0%'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {overview?.completed_tasks ?? 0} of {overview?.total_tasks ?? 0} tasks
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-400 font-medium">Completed</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">
            {overview?.completed_tasks ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Net: {overview?.net_completions_in_period ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-400 font-medium">Pending</span>
            <Clock className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-amber-400">
            {overview?.pending_tasks ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Active backlog</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] text-slate-400 font-medium">Overdue</span>
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-xl font-bold text-rose-400">
            {overview?.overdue_tasks ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Needs action</div>
        </div>
      </div>
    </WidgetContainer>
  );
};
