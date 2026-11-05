import React, { useState } from 'react';
import { Flame, Award, Calendar, CheckSquare } from 'lucide-react';
import { ConsistencyAnalyticsResponse, HeatmapCell } from '../../types/analytics';

interface ProductivityHeatmapProps {
  consistency: ConsistencyAnalyticsResponse | null;
  loading: boolean;
}

export const ProductivityHeatmap: React.FC<ProductivityHeatmapProps> = ({
  consistency,
  loading,
}) => {
  const [hoveredCell, setHoveredCell] = useState<HeatmapCell | null>(null);

  if (loading && !consistency) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-64 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading consistency data...</span>
      </div>
    );
  }

  if (!consistency) {
    return null;
  }

  const {
    current_streak_days,
    longest_streak_days,
    most_productive_weekday,
    total_productive_days,
    heatmap_365_days,
    timezone,
  } = consistency;

  // Level colors (0 to 4)
  const getLevelColor = (level: number) => {
    switch (level) {
      case 1:
        return 'bg-emerald-950/80 border-emerald-900/60 hover:border-emerald-600 text-emerald-400';
      case 2:
        return 'bg-emerald-800/80 border-emerald-700/60 hover:border-emerald-400 text-emerald-200';
      case 3:
        return 'bg-emerald-600 border-emerald-500 hover:border-emerald-300 text-white';
      case 4:
        return 'bg-emerald-400 border-emerald-300 hover:border-white text-slate-950';
      default:
        return 'bg-slate-900/90 border-slate-800 hover:border-slate-700 text-slate-600';
    }
  };

  // Group 365 cells into columns of 7 days (weeks)
  const weeks: HeatmapCell[][] = [];
  let currentWeek: HeatmapCell[] = [];

  heatmap_365_days.forEach((cell, idx) => {
    currentWeek.push(cell);
    if (currentWeek.length === 7 || idx === heatmap_365_days.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-5">
      {/* Metrics Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <span>Productivity Consistency & Streaks</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
              {timezone}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Year-round habit tracking and 365-day completion intensity.
          </p>
        </div>

        {/* Consistency Stat Badges */}
        <div className="grid grid-cols-2 sm:flex sm:items-center gap-2.5 text-xs">
          <div className="px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="text-[10px] text-amber-400/80 block uppercase tracking-wider font-semibold">
                Current Streak
              </span>
              <span className="text-sm font-bold text-white">
                {current_streak_days} {current_streak_days === 1 ? 'day' : 'days'}
              </span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
            <Award className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <span className="text-[10px] text-emerald-400/80 block uppercase tracking-wider font-semibold">
                Best Streak
              </span>
              <span className="text-sm font-bold text-white">
                {longest_streak_days} {longest_streak_days === 1 ? 'day' : 'days'}
              </span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-400 shrink-0" />
            <div>
              <span className="text-[10px] text-indigo-400/80 block uppercase tracking-wider font-semibold">
                Top Day
              </span>
              <span className="text-sm font-bold text-white">
                {most_productive_weekday || 'N/A'}
              </span>
            </div>
          </div>

          <div className="px-3 py-2 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-teal-400 shrink-0" />
            <div>
              <span className="text-[10px] text-teal-400/80 block uppercase tracking-wider font-semibold">
                Active Days
              </span>
              <span className="text-sm font-bold text-white">
                {total_productive_days}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Heatmap Grid (horizontally scrollable on small screens) */}
      <div className="space-y-2">
        <div className="overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-800">
          <div className="min-w-[720px] flex gap-[3px] py-1">
            {weeks.map((week, wIdx) => (
              <div key={wIdx} className="flex flex-col gap-[3px]">
                {week.map((cell) => (
                  <div
                    key={cell.date}
                    className={`w-3 h-3 rounded-[2.5px] border transition cursor-pointer ${getLevelColor(
                      cell.level
                    )}`}
                    onMouseEnter={() => setHoveredCell(cell)}
                    onMouseLeave={() => setHoveredCell(null)}
                    title={`${cell.date}: ${cell.count} completion ${
                      cell.count === 1 ? 'event' : 'events'
                    }`}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Heatmap Footer Legend & Hover Status */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 pt-1 gap-2">
          <div className="h-5 flex items-center">
            {hoveredCell ? (
              <span className="text-emerald-400 font-medium">
                {hoveredCell.date}:{' '}
                <strong className="text-white">
                  {hoveredCell.count} completion {hoveredCell.count === 1 ? 'event' : 'events'}
                </strong>{' '}
                (intensity level {hoveredCell.level})
              </span>
            ) : (
              <span className="text-slate-500">
                Hover over a cell to view daily completed task events
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 self-end sm:self-auto">
            <span className="text-[11px] text-slate-500">Less</span>
            <div className="w-2.5 h-2.5 rounded-[2px] bg-slate-900 border border-slate-800" />
            <div className="w-2.5 h-2.5 rounded-[2px] bg-emerald-950 border border-emerald-900/60" />
            <div className="w-2.5 h-2.5 rounded-[2px] bg-emerald-800 border border-emerald-700/60" />
            <div className="w-2.5 h-2.5 rounded-[2px] bg-emerald-600 border border-emerald-500" />
            <div className="w-2.5 h-2.5 rounded-[2px] bg-emerald-400 border border-emerald-300" />
            <span className="text-[11px] text-slate-500">More</span>
          </div>
        </div>
      </div>
    </div>
  );
};

