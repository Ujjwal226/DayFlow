import React from 'react';
import { Target, CheckCircle2, AlertTriangle, TrendingUp, Award } from 'lucide-react';
import { GoalAnalyticsOverview } from '../../types/goal';

interface GoalAnalyticsCardProps {
  analytics: GoalAnalyticsOverview | null;
  isLoading?: boolean;
}

export const GoalAnalyticsCard: React.FC<GoalAnalyticsCardProps> = ({ analytics, isLoading }) => {
  if (isLoading || !analytics) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/4 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-16 bg-slate-800/50 rounded-xl" />
          <div className="h-16 bg-slate-800/50 rounded-xl" />
          <div className="h-16 bg-slate-800/50 rounded-xl" />
          <div className="h-16 bg-slate-800/50 rounded-xl" />
        </div>
      </div>
    );
  }

  const completionRate = Math.round(analytics.completion_rate);
  const avgProgress = Math.round(analytics.average_progress_percentage);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-5">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold text-white">Strategic Goals Overview</h2>
        </div>
        <span className="text-xs text-slate-400">
          {analytics.total_goals} Total Defined Goals
        </span>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Active Goals</span>
            <Target className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">{analytics.active_goals}</div>
          <div className="text-[11px] text-slate-500 mt-1">In progress & on track</div>
        </div>

        <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Completed</span>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-teal-400">{analytics.completed_goals}</div>
          <div className="text-[11px] text-slate-500 mt-1">{completionRate}% total completion rate</div>
        </div>

        <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Average Progress</span>
            <Award className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{avgProgress}%</div>
          <div className="text-[11px] text-slate-500 mt-1">Across all open goals</div>
        </div>

        <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>At Risk</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">{analytics.at_risk_goals}</div>
          <div className="text-[11px] text-slate-500 mt-1">Requiring immediate focus</div>
        </div>
      </div>

      {/* Breakdown Bar: Categories */}
      {analytics.categories && analytics.categories.length > 0 && (
        <div className="pt-4 border-t border-slate-800/80">
          <div className="text-xs text-slate-400 mb-2 font-medium">Goals by Category</div>
          <div className="flex flex-wrap gap-2">
            {analytics.categories.map((c) => (
              <span
                key={c.category}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-800/60 border border-slate-700/60 rounded-lg text-xs text-slate-300 capitalize"
              >
                <span>{c.category.toLowerCase()}</span>
                <span className="bg-slate-700/80 text-white font-semibold text-[10px] px-1.5 py-0.2 rounded-full">
                  {c.count}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
