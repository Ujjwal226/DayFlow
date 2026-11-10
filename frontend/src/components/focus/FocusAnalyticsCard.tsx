import React from 'react';
import { Target, Flame, BarChart3, Folder, CheckSquare } from 'lucide-react';
import { FocusAnalyticsOverview } from '../../types/focus';

interface FocusAnalyticsCardProps {
  analytics: FocusAnalyticsOverview | null;
}

export const FocusAnalyticsCard: React.FC<FocusAnalyticsCardProps> = ({ analytics }) => {
  if (!analytics) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 flex items-center justify-center min-h-[300px]">
        <span className="text-sm text-gray-500">Loading focus analytics...</span>
      </div>
    );
  }

  const { daily, weekly, task_breakdown, project_breakdown } = analytics;
  const maxWeeklyMinutes = Math.max(
    ...weekly.days.map((d) => d.focus_minutes),
    daily.daily_goal_minutes || 60,
    1
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-500" />
          Focus Analytics & Goals
        </h3>
        <div className="flex items-center gap-1 px-2.5 py-1 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-full text-xs font-bold text-amber-700 dark:text-amber-400">
          <Flame className="w-3.5 h-3.5 fill-current" />
          <span>{daily.streak_days} Day Streak</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1">Today's Focus</span>
          <span className="text-2xl font-extrabold text-gray-900 dark:text-white flex items-baseline gap-1">
            {Math.round(daily.today_focus_seconds / 60)} <span className="text-xs font-medium text-gray-400">min</span>
          </span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1">Sessions Done</span>
          <span className="text-2xl font-extrabold text-gray-900 dark:text-white flex items-baseline gap-1">
            {daily.today_completed_sessions} <span className="text-xs font-medium text-gray-400">done</span>
          </span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1">Week Total</span>
          <span className="text-2xl font-extrabold text-gray-900 dark:text-white flex items-baseline gap-1">
            {weekly.total_focus_minutes} <span className="text-xs font-medium text-gray-400">min</span>
          </span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1">Avg Session</span>
          <span className="text-2xl font-extrabold text-gray-900 dark:text-white flex items-baseline gap-1">
            {weekly.average_session_minutes} <span className="text-xs font-medium text-gray-400">min</span>
          </span>
        </div>
      </div>

      {/* Daily Goal Progress Bar */}
      <div>
        <div className="flex justify-between items-center text-xs font-semibold mb-2 text-gray-600 dark:text-gray-400">
          <span className="flex items-center gap-1.5">
            <Target className="w-4 h-4 text-indigo-500" />
            Today's Goal ({daily.daily_goal_minutes}m target)
          </span>
          <span>{daily.goal_completion_percentage}%</span>
        </div>
        <div className="w-full bg-gray-100 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              daily.goal_completion_percentage >= 100 ? 'bg-emerald-500' : 'bg-indigo-600'
            }`}
            style={{ width: `${Math.min(daily.goal_completion_percentage, 100)}%` }}
          />
        </div>
      </div>

      {/* 7-Day Trend Chart */}
      <div>
        <h4 className="text-xs font-bold text-gray-400 dark:text-gray-400 uppercase tracking-wider mb-3">
          7-Day Trend (Minutes)
        </h4>
        <div className="flex items-end justify-between gap-2 h-32 pt-4 border-b border-gray-100 dark:border-gray-700">
          {weekly.days.map((item) => {
            const heightPercent = Math.max(5, (item.focus_minutes / maxWeeklyMinutes) * 100);
            return (
              <div key={item.date} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                <span className="text-[10px] font-semibold text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {item.focus_minutes}m
                </span>
                <div
                  className="w-full max-w-[28px] bg-indigo-500/80 group-hover:bg-indigo-600 rounded-t-md transition-all duration-300"
                  style={{ height: `${heightPercent}%` }}
                />
                <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
                  {item.date.slice(5)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Task & Project Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Task Breakdown */}
        <div className="bg-gray-50 dark:bg-gray-700/30 rounded-xl p-4">
          <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <CheckSquare className="w-3.5 h-3.5" />
            Top Focused Tasks
          </h5>
          {task_breakdown.length === 0 ? (
            <p className="text-xs text-gray-400 italic">No task sessions logged this week</p>
          ) : (
            <div className="space-y-2">
              {task_breakdown.slice(0, 4).map((t) => (
                <div key={t.task_id || t.task_title} className="flex justify-between items-center text-xs">
                  <span className="text-gray-800 dark:text-gray-200 truncate max-w-[160px] font-medium">
                    {t.task_title}
                  </span>
                  <span className="text-gray-500 font-semibold">{t.total_focus_minutes} min</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Project Breakdown */}
        <div className="bg-gray-50 dark:bg-gray-700/30 rounded-xl p-4">
          <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Folder className="w-3.5 h-3.5" />
            Project Distribution
          </h5>
          {project_breakdown.length === 0 ? (
            <p className="text-xs text-gray-400 italic">No project sessions logged this week</p>
          ) : (
            <div className="space-y-2">
              {project_breakdown.slice(0, 4).map((p) => (
                <div key={p.project_id || p.project_name} className="flex justify-between items-center text-xs">
                  <span className="text-gray-800 dark:text-gray-200 truncate max-w-[160px] font-medium">
                    {p.project_name}
                  </span>
                  <span className="text-gray-500 font-semibold">{p.total_focus_minutes} min</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
