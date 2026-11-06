import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../../api/analytics';
import { ProductivityTrendsResponse } from '../../../types/analytics';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { ArrowRight, BarChart2 } from 'lucide-react';
import { TrendChartSkeleton } from '../WidgetSkeletons';

export const ProductivityTrendsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [trends, setTrends] = useState<ProductivityTrendsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrends = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.getTrends({ interval: 'daily', days: 7 });
      setTrends(res);
    } catch {
      setError('Unable to load productivity trends.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, []);

  const buckets = trends?.buckets ?? [];
  const maxNet = Math.max(...buckets.map((b) => Math.max(0, b.net_completions)), 5);

  return (
    <WidgetContainer
      title="Productivity Trends"
      description="Trailing 7-day completion velocity"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<TrendChartSkeleton />}
      error={error}
      onRetry={fetchTrends}
      headerAction={
        <Link
          to="/analytics"
          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
        >
          <span>Deep Dive</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {buckets.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <BarChart2 className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-medium text-slate-400">No trend data available</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-end justify-between gap-2 h-28 pt-4 px-2">
            {buckets.map((b) => {
              const val = Math.max(0, b.net_completions);
              const heightPercent = Math.min(100, Math.round((val / maxNet) * 100));
              const label = new Date(b.start_date).toLocaleDateString(undefined, {
                weekday: 'narrow',
              });

              return (
                <div key={b.start_date} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group">
                  <span className="text-[10px] text-slate-400 group-hover:text-emerald-400 transition font-mono">
                    {b.net_completions}
                  </span>
                  <div className="w-full max-w-[28px] bg-slate-800 rounded-t-md overflow-hidden flex items-end h-20">
                    <div
                      className="w-full bg-emerald-500/80 group-hover:bg-emerald-400 transition-all rounded-t-md"
                      style={{ height: `${Math.max(8, heightPercent)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-500 font-medium">{label}</span>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
            <span>Daily net task completions</span>
            <span className="text-emerald-400 font-medium">
              Comparison: {trends?.comparison.current_period_completions ?? 0}
            </span>
          </div>
        </div>
      )}
    </WidgetContainer>
  );
};
