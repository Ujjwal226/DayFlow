/**
 * 7-day completion trend chart using Recharts ComposedChart.
 * Bars for completed / pending counts, line for completion % rate.
 */
import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { DailyMetric } from '../../types/api';
import { useTheme } from '../../context/ThemeContext';
import { TrendingUp, CheckCircle2, Calendar } from 'lucide-react';
import { formatDate } from '../../lib/utils';

interface Props {
  data: DailyMetric[];
}

export const CompletionTrendChart: React.FC<Props> = ({ data }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const gridColor   = isDark ? '#2e2e42' : '#e4e6f0';
  const axisColor   = isDark ? '#9898b8' : '#4a4d6a';
  const tooltipBg   = isDark ? '#16161e' : '#ffffff';
  const tooltipBdr  = isDark ? '#2e2e42' : '#e4e6f0';
  const tooltipText = isDark ? '#e8e8f0' : '#1a1b2e';

  const totalCompleted = data.reduce((s, d) => s + d.completed, 0);
  const totalAll       = data.reduce((s, d) => s + d.total, 0);
  const avgRate        = totalAll > 0 ? Math.round((totalCompleted / totalAll) * 100) : 0;

  const chartData = data.map((d) => ({
    ...d,
    label: `${d.day_name} ${d.date.slice(5)}`,
  }));

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2 text-violet-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <TrendingUp className="w-4 h-4" />
            <span>7-Day Trend</span>
          </div>
          <h2 className="text-base font-bold tracking-tight text-[var(--text-primary)]">
            Completion History
          </h2>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Completed vs pending tasks per day, with overall rate trend.
          </p>
        </div>

        {/* 7-day summary pill */}
        <div className="flex items-center gap-3 bg-[var(--bg-elevated)] px-3.5 py-2 rounded-xl border border-[var(--bg-border)] self-start sm:self-auto shrink-0">
          <span className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <strong className="text-[var(--text-primary)]">{totalCompleted}</strong>
            <span>/ {totalAll} done</span>
          </span>
          <span className="text-[var(--text-muted)]">·</span>
          <span className="text-xs font-semibold text-violet-500">{avgRate}% avg</span>
        </div>
      </div>

      {/* Chart */}
      <div className="w-full h-64 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gradComp" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#059669" stopOpacity={0.65} />
              </linearGradient>
              <linearGradient id="gradPend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.85} />
                <stop offset="100%" stopColor="#d97706" stopOpacity={0.55} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />

            <XAxis
              dataKey="label"
              stroke={axisColor}
              tick={{ fontSize: 11, fill: axisColor }}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
            />

            {/* Left axis – task counts */}
            <YAxis
              yAxisId="count"
              allowDecimals={false}
              stroke={axisColor}
              tick={{ fontSize: 11, fill: axisColor }}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
            />

            {/* Right axis – completion % */}
            <YAxis
              yAxisId="rate"
              orientation="right"
              domain={[0, 100]}
              stroke="#a78bfa"
              tick={{ fontSize: 10, fill: '#a78bfa' }}
              tickFormatter={(v) => `${v}%`}
              tickLine={false}
              axisLine={false}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload as DailyMetric & { label: string };
                return (
                  <div
                    className="rounded-xl border p-3 text-xs shadow-xl space-y-1.5"
                    style={{ background: tooltipBg, borderColor: tooltipBdr, color: tooltipText }}
                  >
                    <div className="flex items-center gap-1.5 font-semibold border-b pb-1.5"
                         style={{ borderColor: tooltipBdr }}>
                      <Calendar className="w-3.5 h-3.5 text-violet-500" />
                      <span>{formatDate(d.date)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="flex items-center gap-1 text-emerald-500">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                        Completed:
                      </span>
                      <strong className="text-emerald-500">{d.completed}</strong>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="flex items-center gap-1 text-amber-500">
                        <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                        Pending:
                      </span>
                      <strong className="text-amber-500">{d.pending}</strong>
                    </div>
                    <div className="flex justify-between gap-4 pt-1 border-t" style={{ borderColor: tooltipBdr }}>
                      <span className="text-violet-400">Completion:</span>
                      <strong className="text-violet-400">{d.completion_percentage}%</strong>
                    </div>
                  </div>
                );
              }}
            />

            <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ fontSize: '11px', paddingBottom: '10px' }} />

            <Bar yAxisId="count" dataKey="completed" name="Completed" fill="url(#gradComp)" radius={[4, 4, 0, 0]} maxBarSize={26} />
            <Bar yAxisId="count" dataKey="pending"   name="Pending"   fill="url(#gradPend)" radius={[4, 4, 0, 0]} maxBarSize={26} />
            <Line
              yAxisId="rate"
              type="monotone"
              dataKey="completion_percentage"
              name="Rate %"
              stroke="#8b5cf6"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#8b5cf6', stroke: '#fff', strokeWidth: 1.5 }}
              activeDot={{ r: 6, fill: '#a78bfa' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
