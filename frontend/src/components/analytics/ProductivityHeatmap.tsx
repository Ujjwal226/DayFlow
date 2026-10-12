/**
 * Productivity calendar heatmap.
 * Renders a GitHub-style grid of the last N days (default 84 = 12 weeks)
 * where each cell is coloured by task-completion intensity (0–4).
 */
import React, { useState } from 'react';
import type { HeatmapDay } from '../../types/api';
import { formatDate } from '../../lib/utils';
import { Activity } from 'lucide-react';

interface Props {
  data: HeatmapDay[];
}

/** Tailwind-safe colour classes for dark / light theme per intensity level */
const INTENSITY_DARK: Record<number, string> = {
  0: 'bg-[var(--bg-elevated)] border-[var(--bg-border)]',
  1: 'bg-emerald-900/60 border-emerald-800/50',
  2: 'bg-emerald-700/70 border-emerald-600/50',
  3: 'bg-emerald-500/80 border-emerald-400/60',
  4: 'bg-emerald-400    border-emerald-300/60',
};

const INTENSITY_LIGHT: Record<number, string> = {
  0: 'bg-slate-100 border-slate-200',
  1: 'bg-emerald-100 border-emerald-200',
  2: 'bg-emerald-300 border-emerald-400',
  3: 'bg-emerald-500 border-emerald-600',
  4: 'bg-emerald-600 border-emerald-700',
};

/** Return the ISO week-day index (Mon=0 … Sun=6) for a YYYY-MM-DD string */
function weekdayIndex(dateStr: string): number {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dow = new Date(y, m - 1, d).getDay(); // 0=Sun … 6=Sat
  return dow === 0 ? 6 : dow - 1;             // shift so Mon=0
}

/** Group flat day array into ISO weeks (arrays of up to 7 days) */
function groupByWeek(days: HeatmapDay[]): Array<Array<HeatmapDay | null>> {
  if (!days.length) return [];

  const weeks: Array<Array<HeatmapDay | null>> = [];
  let week: Array<HeatmapDay | null> = [];

  // Pad the first week with nulls if the first day is not Monday
  const firstDow = weekdayIndex(days[0].date);
  for (let i = 0; i < firstDow; i++) week.push(null);

  for (const day of days) {
    week.push(day);
    if (week.length === 7) {
      weeks.push(week);
      week = [];
    }
  }
  // Pad the last week
  if (week.length > 0) {
    while (week.length < 7) week.push(null);
    weeks.push(week);
  }
  return weeks;
}

/** Derive month labels from the first day of each week */
function monthLabels(weeks: Array<Array<HeatmapDay | null>>): Array<{ label: string; col: number }> {
  const labels: Array<{ label: string; col: number }> = [];
  let lastMonth = -1;
  weeks.forEach((week, col) => {
    const day = week.find(Boolean) as HeatmapDay | undefined;
    if (!day) return;
    const [, m, d] = day.date.split('-').map(Number);
    if (m !== lastMonth && d <= 7) {
      labels.push({
        label: new Date(+day.date.slice(0, 4), m - 1, 1).toLocaleString('en', { month: 'short' }),
        col,
      });
      lastMonth = m;
    }
  });
  return labels;
}

const DOW_LABELS = ['Mon', 'Wed', 'Fri'];
const DOW_ROWS   = [0, 2, 4]; // indices that get a label

export const ProductivityHeatmap: React.FC<Props> = ({ data }) => {
  const [tooltip, setTooltip] = useState<HeatmapDay | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Detect dark mode via CSS variable presence (avoids importing ThemeContext here)
  const isDark =
    typeof document !== 'undefined' &&
    !document.documentElement.classList.contains('light');

  const INTENSITY = isDark ? INTENSITY_DARK : INTENSITY_LIGHT;

  const weeks     = groupByWeek(data);
  const mLabels   = monthLabels(weeks);

  const totalCompleted = data.reduce((s, d) => s + d.completed_count, 0);
  const activeDays     = data.filter((d) => d.completed_count > 0).length;

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2 text-violet-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <Activity className="w-4 h-4" />
            <span>Activity Calendar</span>
          </div>
          <h2 className="text-base font-bold tracking-tight text-[var(--text-primary)]">
            Productivity Heatmap
          </h2>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Tasks completed each day over the last 12 weeks.
          </p>
        </div>

        {/* Summary */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-center">
            <p className="text-xl font-extrabold text-emerald-500">{totalCompleted}</p>
            <p className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wide">Completed</p>
          </div>
          <div className="w-px h-8 bg-[var(--bg-border)]" />
          <div className="text-center">
            <p className="text-xl font-extrabold text-violet-500">{activeDays}</p>
            <p className="text-[10px] text-[var(--text-secondary)] uppercase tracking-wide">Active Days</p>
          </div>
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-flex gap-0 min-w-max">
          {/* Day-of-week labels on the left */}
          <div className="flex flex-col mr-1.5 mt-5">
            {[0, 1, 2, 3, 4, 5, 6].map((rowIdx) => (
              <div
                key={rowIdx}
                className="h-[12px] mb-0.5 text-[9px] text-[var(--text-muted)] leading-[12px] w-6 flex items-center"
              >
                {DOW_ROWS.includes(rowIdx) ? DOW_LABELS[DOW_ROWS.indexOf(rowIdx)] : ''}
              </div>
            ))}
          </div>

          {/* Grid columns (one per week) */}
          <div className="flex flex-col">
            {/* Month labels row */}
            <div className="relative h-5 mb-1" style={{ minWidth: `${weeks.length * 14}px` }}>
              {mLabels.map(({ label, col }) => (
                <span
                  key={col}
                  className="absolute text-[9px] text-[var(--text-muted)] uppercase tracking-wide"
                  style={{ left: `${col * 14}px` }}
                >
                  {label}
                </span>
              ))}
            </div>

            {/* The actual grid */}
            <div className="flex gap-0.5">
              {weeks.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-0.5">
                  {week.map((day, di) =>
                    day ? (
                      <div
                        key={day.date}
                        className={`w-3 h-3 rounded-[2px] border cursor-default transition-transform hover:scale-125 ${INTENSITY[day.intensity]}`}
                        onMouseEnter={(e) => {
                          setTooltip(day);
                          setTooltipPos({ x: e.clientX, y: e.clientY });
                        }}
                        onMouseLeave={() => setTooltip(null)}
                        title={`${formatDate(day.date)}: ${day.completed_count} completed`}
                      />
                    ) : (
                      <div key={`empty-${wi}-${di}`} className="w-3 h-3" />
                    )
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Floating tooltip (portal-less, fixed position) */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none"
          style={{ left: tooltipPos.x + 12, top: tooltipPos.y - 60 }}
        >
          <div
            className="rounded-xl border p-2.5 text-xs shadow-xl space-y-1"
            style={{
              background: isDark ? '#16161e' : '#ffffff',
              borderColor: isDark ? '#2e2e42' : '#e4e6f0',
              color: isDark ? '#e8e8f0' : '#1a1b2e',
              minWidth: 160,
            }}
          >
            <p className="font-semibold text-[var(--text-primary)]">{formatDate(tooltip.date)}</p>
            <div className="flex justify-between gap-3">
              <span className="text-emerald-500">Completed:</span>
              <strong className="text-emerald-500">{tooltip.completed_count}</strong>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-secondary)]">Scheduled:</span>
              <span>{tooltip.total_scheduled}</span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-2 mt-4 justify-end">
        <span className="text-[10px] text-[var(--text-muted)]">Less</span>
        {[0, 1, 2, 3, 4].map((lvl) => (
          <div
            key={lvl}
            className={`w-3 h-3 rounded-[2px] border ${INTENSITY[lvl]}`}
          />
        ))}
        <span className="text-[10px] text-[var(--text-muted)]">More</span>
      </div>
    </div>
  );
};
