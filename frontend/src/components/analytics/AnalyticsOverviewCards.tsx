import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  Percent,
  ListTodo,
} from 'lucide-react';
import { ProductivityOverviewResponse } from '../../types/analytics';

interface AnalyticsOverviewCardsProps {
  overview: ProductivityOverviewResponse | null;
  loading: boolean;
}

export const AnalyticsOverviewCards: React.FC<AnalyticsOverviewCardsProps> = ({
  overview,
  loading,
}) => {
  if (loading && !overview) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-28 flex flex-col justify-between"
          >
            <div className="w-8 h-8 rounded-lg bg-slate-800" />
            <div className="space-y-1.5">
              <div className="w-12 h-3 bg-slate-800 rounded" />
              <div className="w-16 h-5 bg-slate-800 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!overview) {
    return null;
  }

  const cards = [
    {
      title: 'Total Tasks',
      value: overview.total_tasks,
      icon: ListTodo,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-500/20',
      description: 'Active root tasks',
    },
    {
      title: 'Completed',
      value: overview.completed_tasks,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20',
      description: 'Completed tasks',
    },
    {
      title: 'Pending',
      value: overview.pending_tasks,
      icon: Clock,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20',
      description: 'Todo & in progress',
    },
    {
      title: 'Overdue',
      value: overview.overdue_tasks,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/10',
      borderColor: 'border-rose-500/20',
      description: 'Pending past due',
    },
    {
      title: 'Cancelled',
      value: overview.cancelled_tasks,
      icon: XCircle,
      color: 'text-slate-400',
      bgColor: 'bg-slate-500/10',
      borderColor: 'border-slate-500/20',
      description: 'Cancelled tasks',
    },
    {
      title: 'Completion Rate',
      value: `${overview.completion_rate}%`,
      icon: Percent,
      color: 'text-teal-400',
      bgColor: 'bg-teal-500/10',
      borderColor: 'border-teal-500/20',
      description: 'Completed / Total active',
    },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className={`p-4 rounded-2xl bg-slate-900/60 border ${card.borderColor} backdrop-blur flex flex-col justify-between transition hover:border-slate-700`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-400">
                  {card.title}
                </span>
                <div className={`p-1.5 rounded-lg ${card.bgColor} ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <span className="text-xl sm:text-2xl font-bold tracking-tight text-white block">
                  {card.value}
                </span>
                <span className="text-[11px] text-slate-500 block truncate mt-0.5">
                  {card.description}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Period-specific summary strip */}
      <div className="px-4 py-2.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Selected Period Activity:</span>
        </div>
        <div className="flex flex-wrap items-center gap-4 sm:gap-6">
          <span className="text-slate-300">
            Created:{' '}
            <strong className="text-white font-semibold">
              {overview.tasks_created_in_period}
            </strong>
          </span>
          <span className="text-slate-300">
            Gross Completed:{' '}
            <strong className="text-emerald-400 font-semibold">
              {overview.tasks_completed_in_period}
            </strong>
          </span>
          <span className="text-slate-300">
            Reopened:{' '}
            <strong className="text-amber-400 font-semibold">
              {overview.tasks_reopened_in_period}
            </strong>
          </span>
          <span className="text-slate-300">
            Net Completed:{' '}
            <strong
              className={`font-semibold ${
                overview.net_completions_in_period < 0
                  ? 'text-rose-400'
                  : 'text-teal-400'
              }`}
            >
              {overview.net_completions_in_period > 0
                ? `+${overview.net_completions_in_period}`
                : overview.net_completions_in_period}
            </strong>
          </span>
        </div>
      </div>
    </div>
  );
};

