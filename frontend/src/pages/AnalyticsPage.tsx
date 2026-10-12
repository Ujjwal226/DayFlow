/**
 * DayFlow – Analytics Page (Stage 4)
 *
 * Displays:
 *   - Summary metric cards (total, completed, pending, overdue)
 *   - Today's daily completion progress ring / bar
 *   - 7-day Recharts completion trend (CompletionTrendChart)
 *   - Productivity calendar heatmap (ProductivityHeatmap)
 *   - Category & priority breakdown (BreakdownPanel)
 *
 * All daily reporting uses Asia/Kolkata as reported by the backend.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart2,
  CheckCircle2,
  Clock,
  AlertCircle,
  ListTodo,
  RefreshCw,
  Loader2,
  CalendarDays,
} from 'lucide-react';
import { analyticsApi } from '../lib/api';
import type { AnalyticsResponse } from '../types/api';
import { CompletionTrendChart } from '../components/analytics/CompletionTrendChart';
import { ProductivityHeatmap } from '../components/analytics/ProductivityHeatmap';
import { BreakdownPanel } from '../components/analytics/BreakdownPanel';
import { toast } from 'sonner';

// ─── Metric card ─────────────────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: number | string;
  sub: string;
  icon: React.ReactNode;
  color: string; // Tailwind bg/text pair e.g. "violet"
}

const COLOR_CLASSES: Record<string, { bg: string; text: string; borderHover: string }> = {
  violet: {
    bg: 'bg-violet-500/10',
    text: 'text-violet-500',
    borderHover: 'hover:border-violet-500/30',
  },
  emerald: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500',
    borderHover: 'hover:border-emerald-500/30',
  },
  amber: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    borderHover: 'hover:border-amber-500/30',
  },
  rose: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-500',
    borderHover: 'hover:border-rose-500/30',
  },
};

const MetricCard: React.FC<MetricCardProps> = ({ label, value, sub, icon, color }) => {
  const styles = COLOR_CLASSES[color] || COLOR_CLASSES.violet;

  return (
    <div
      className={`p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm
        ${styles.borderHover} transition-all`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
          {label}
        </span>
        <div className={`w-8 h-8 rounded-lg ${styles.bg} ${styles.text} flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <p className="text-2xl sm:text-3xl font-extrabold text-[var(--text-primary)] mt-3 tracking-tight">
        {value}
      </p>
      <p className="text-xs text-[var(--text-secondary)] mt-1">{sub}</p>
    </div>
  );
};

// ─── Today's radial completion ───────────────────────────────────────────────

interface DailyProgressProps {
  completed: number;
  total: number;
  pct: number;
}

const DailyProgress: React.FC<DailyProgressProps> = ({ completed, total, pct }) => {
  const radius = 52;
  const circ   = 2 * Math.PI * radius;
  const dash   = circ * (pct / 100);

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm flex flex-col items-center justify-center gap-4">
      <div className="flex items-center gap-2 text-violet-500 text-xs font-semibold uppercase tracking-wider self-start">
        <CalendarDays className="w-4 h-4" />
        <span>Today's Progress</span>
      </div>

      {/* SVG ring */}
      <div className="relative flex items-center justify-center">
        <svg width="140" height="140" className="-rotate-90">
          {/* Track */}
          <circle
            cx="70" cy="70" r={radius}
            fill="none"
            stroke="var(--bg-elevated)"
            strokeWidth="10"
          />
          {/* Progress */}
          <circle
            cx="70" cy="70" r={radius}
            fill="none"
            stroke="url(#ringGrad)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            className="transition-all duration-700"
          />
          <defs>
            <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor="#4f46e5" />
            </linearGradient>
          </defs>
        </svg>
        {/* Centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight">
            {pct}%
          </span>
          <span className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
            done
          </span>
        </div>
      </div>

      <p className="text-sm text-[var(--text-secondary)] text-center">
        {completed} of {total} tasks completed today
      </p>
    </div>
  );
};

// ─── AnalyticsPage ────────────────────────────────────────────────────────────

export const AnalyticsPage: React.FC = () => {
  const [data,       setData]       = useState<AnalyticsResponse | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  const fetchAnalytics = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else           setLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.get(84);
      setData(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load analytics';
      setError(msg);
      if (isRefresh) toast.error('Failed to refresh analytics: ' + msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-violet-500 font-medium text-xs tracking-wider uppercase mb-1">
            <BarChart2 className="w-4 h-4" />
            <span>Productivity Insights</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Analytics
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Real-time task metrics and productivity trends · Asia/Kolkata
          </p>
        </div>

        <button
          type="button"
          onClick={() => fetchAnalytics(true)}
          disabled={refreshing || loading}
          className="self-start sm:self-auto flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[var(--bg-border)] text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none disabled:opacity-50"
          aria-label="Refresh analytics"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* ── Loading state ────────────────────────────────────────────── */}
      {loading && (
        <div className="flex flex-col items-center justify-center p-20 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)]">
          <Loader2 className="w-9 h-9 animate-spin text-violet-500 mb-3" />
          <p className="text-sm text-[var(--text-secondary)]">Loading analytics…</p>
        </div>
      )}

      {/* ── Error state ──────────────────────────────────────────────── */}
      {!loading && error && (
        <div className="p-8 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
          <p className="text-sm text-rose-500 font-medium">{error}</p>
          <button
            type="button"
            onClick={() => fetchAnalytics()}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Data ─────────────────────────────────────────────────────── */}
      {!loading && !error && data && (
        <>
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Total Tasks"
              value={data.summary.total}
              sub="All active tasks"
              icon={<ListTodo className="w-4 h-4" />}
              color="violet"
            />
            <MetricCard
              label="Completed"
              value={data.summary.completed}
              sub={`${data.summary.completion_percentage}% completion rate`}
              icon={<CheckCircle2 className="w-4 h-4" />}
              color="emerald"
            />
            <MetricCard
              label="Pending"
              value={data.summary.pending}
              sub="Awaiting completion"
              icon={<Clock className="w-4 h-4" />}
              color="amber"
            />
            <MetricCard
              label="Overdue"
              value={data.summary.overdue}
              sub="Past scheduled date"
              icon={<AlertCircle className="w-4 h-4" />}
              color="rose"
            />
          </div>

          {/* Today's Progress + 7-Day Trend */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-1">
              <DailyProgress
                completed={data.today.completed}
                total={data.today.total}
                pct={data.today.completion_percentage}
              />
            </div>
            <div className="lg:col-span-3">
              <CompletionTrendChart data={data.seven_day_trend} />
            </div>
          </div>

          {/* Productivity Calendar Heatmap */}
          <ProductivityHeatmap data={data.heatmap} />

          {/* Category & Priority Breakdown */}
          <BreakdownPanel
            categories={data.category_breakdown}
            priorities={data.priority_breakdown}
          />

          {/* Footer note */}
          <p className="text-center text-xs text-[var(--text-muted)] pb-2">
            All daily metrics are calculated in{' '}
            <span className="font-semibold text-[var(--text-secondary)]">Asia/Kolkata (UTC+05:30)</span>.
            Data excludes soft-deleted tasks.
          </p>
        </>
      )}
    </div>
  );
};
