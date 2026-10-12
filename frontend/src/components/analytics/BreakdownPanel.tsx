/**
 * Compact category & priority breakdown bars.
 * Shown as horizontal progress bars with counts.
 */
import React from 'react';
import type { CategoryMetric, PriorityMetric } from '../../types/api';
import { BarChart2 } from 'lucide-react';

// ─── Category colours ────────────────────────────────────────────────────────

const CAT_COLORS: Record<string, { bar: string; badge: string }> = {
  work:     { bar: 'from-violet-600 to-violet-500',   badge: 'bg-violet-500/15 text-violet-400 border-violet-500/20' },
  personal: { bar: 'from-sky-600    to-sky-500',      badge: 'bg-sky-500/15    text-sky-400    border-sky-500/20'    },
  learning: { bar: 'from-indigo-600 to-indigo-500',   badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20' },
  health:   { bar: 'from-teal-600   to-teal-500',     badge: 'bg-teal-500/15   text-teal-400   border-teal-500/20'  },
  other:    { bar: 'from-slate-600  to-slate-500',    badge: 'bg-slate-500/15  text-slate-400  border-slate-500/20' },
};

const PRIO_COLORS: Record<string, { bar: string; badge: string }> = {
  high:   { bar: 'from-rose-600   to-rose-500',   badge: 'bg-rose-500/15   text-rose-400   border-rose-500/20'   },
  medium: { bar: 'from-amber-500  to-amber-400',  badge: 'bg-amber-500/15  text-amber-400  border-amber-500/20'  },
  low:    { bar: 'from-emerald-600 to-emerald-500', badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20' },
};

// ─── Generic breakdown row ───────────────────────────────────────────────────

interface BreakdownRowProps {
  label: string;
  total: number;
  completed: number;
  pending: number;
  maxTotal: number;
  colors: { bar: string; badge: string };
}

const BreakdownRow: React.FC<BreakdownRowProps> = ({
  label, total, completed, pending, maxTotal, colors,
}) => {
  const pct = total > 0 ? (completed / total) * 100 : 0;
  const widthPct = maxTotal > 0 ? (total / maxTotal) * 100 : 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span
            className={`capitalize px-2 py-0.5 rounded-md text-[11px] font-semibold border ${colors.badge}`}
          >
            {label}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[var(--text-secondary)]">
          <span className="text-emerald-500 font-medium">{completed}✓</span>
          <span className="text-amber-500 font-medium">{pending}⏳</span>
          <span className="font-semibold text-[var(--text-primary)]">{total}</span>
        </div>
      </div>

      {/* Segmented bar: completed (green) + pending (amber) */}
      <div
        className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden border border-[var(--bg-border)]/50"
        title={`${Math.round(pct)}% complete`}
      >
        <div
          className="h-full flex"
          style={{ width: `${widthPct}%` }}
        >
          {/* Completed portion */}
          <div
            className={`h-full bg-gradient-to-r ${colors.bar} rounded-l-full transition-all duration-500`}
            style={{ width: `${pct}%`, minWidth: completed > 0 ? '4px' : '0' }}
          />
          {/* Pending portion */}
          <div
            className="h-full bg-amber-500/40 rounded-r-full transition-all duration-500"
            style={{ width: `${100 - pct}%`, minWidth: pending > 0 ? '4px' : '0' }}
          />
        </div>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

interface Props {
  categories: CategoryMetric[];
  priorities: PriorityMetric[];
}

export const BreakdownPanel: React.FC<Props> = ({ categories, priorities }) => {
  const maxCatTotal  = Math.max(...categories.map((c) => c.total), 1);
  const maxPrioTotal = Math.max(...priorities.map((p) => p.total), 1);

  // Only show rows with at least one task
  const activeCats  = categories.filter((c) => c.total > 0);
  const activePrios = priorities.filter((p) => p.total > 0);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      {/* Categories */}
      <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div>
          <div className="flex items-center gap-2 text-violet-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <BarChart2 className="w-4 h-4" />
            <span>By Category</span>
          </div>
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Task Distribution</h3>
        </div>

        {activeCats.length === 0 ? (
          <p className="text-xs text-[var(--text-secondary)] py-4 text-center">No tasks yet.</p>
        ) : (
          <div className="space-y-3">
            {activeCats.map((c) => (
              <BreakdownRow
                key={c.category}
                label={c.category}
                total={c.total}
                completed={c.completed}
                pending={c.pending}
                maxTotal={maxCatTotal}
                colors={CAT_COLORS[c.category] ?? CAT_COLORS.other}
              />
            ))}
          </div>
        )}
      </div>

      {/* Priorities */}
      <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div>
          <div className="flex items-center gap-2 text-violet-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <BarChart2 className="w-4 h-4" />
            <span>By Priority</span>
          </div>
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Priority Breakdown</h3>
        </div>

        {activePrios.length === 0 ? (
          <p className="text-xs text-[var(--text-secondary)] py-4 text-center">No tasks yet.</p>
        ) : (
          <div className="space-y-3">
            {activePrios.map((p) => (
              <BreakdownRow
                key={p.priority}
                label={p.priority}
                total={p.total}
                completed={p.completed}
                pending={p.pending}
                maxTotal={maxPrioTotal}
                colors={PRIO_COLORS[p.priority] ?? PRIO_COLORS.medium}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
