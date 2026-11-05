import React from 'react';
import {
  Briefcase,
  AlertOctagon,
  AlertTriangle,
  Clock,
  CalendarDays,
  CalendarCheck,
  CalendarOff,
} from 'lucide-react';
import { WorkloadAnalyticsResponse } from '../../types/analytics';

interface WorkloadSectionProps {
  workloadData: WorkloadAnalyticsResponse | null;
  loading: boolean;
}

export const WorkloadSection: React.FC<WorkloadSectionProps> = ({
  workloadData,
  loading,
}) => {
  if (loading && !workloadData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-56 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading workload metrics...</span>
      </div>
    );
  }

  if (!workloadData) {
    return null;
  }

  const { total_pending_tasks, priority_distribution, horizons, timezone } =
    workloadData;

  const priorities = [
    {
      label: 'Urgent',
      count: priority_distribution.urgent,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/10',
      borderColor: 'border-rose-500/20',
      icon: AlertOctagon,
    },
    {
      label: 'High',
      count: priority_distribution.high,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20',
      icon: AlertTriangle,
    },
    {
      label: 'Medium',
      count: priority_distribution.medium,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-500/20',
      icon: Clock,
    },
    {
      label: 'Low',
      count: priority_distribution.low,
      color: 'text-slate-400',
      bgColor: 'bg-slate-500/10',
      borderColor: 'border-slate-500/20',
      icon: Briefcase,
    },
  ];

  const horizonItems = [
    {
      label: 'Overdue',
      count: horizons.overdue,
      badgeColor:
        horizons.overdue > 0
          ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
          : 'bg-slate-800 text-slate-400 border-slate-700',
      icon: AlertTriangle,
    },
    {
      label: 'Due Today',
      count: horizons.due_today,
      badgeColor:
        horizons.due_today > 0
          ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
          : 'bg-slate-800 text-slate-400 border-slate-700',
      icon: CalendarCheck,
    },
    {
      label: 'Due Tomorrow',
      count: horizons.due_tomorrow,
      badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
      icon: Clock,
    },
    {
      label: 'Next 7 Days',
      count: horizons.due_next_7_days,
      badgeColor: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
      icon: CalendarDays,
    },
    {
      label: 'Due Later',
      count: horizons.due_later,
      badgeColor: 'bg-slate-800 text-slate-300 border-slate-700',
      icon: CalendarDays,
    },
    {
      label: 'No Due Date',
      count: horizons.no_due_date,
      badgeColor: 'bg-slate-900 text-slate-400 border-slate-800',
      icon: CalendarOff,
    },
  ];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-indigo-400" />
            <span>Workload & Deadlines</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-normal">
              {total_pending_tasks} active pending {total_pending_tasks === 1 ? 'task' : 'tasks'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Breakdown of active TODO and IN_PROGRESS tasks by priority and mutually exclusive horizons ({timezone}).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Priority Distribution */}
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Priority Breakdown
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {priorities.map((p) => {
              const Icon = p.icon;
              return (
                <div
                  key={p.label}
                  className={`p-3 rounded-lg bg-slate-900/80 border ${p.borderColor} flex flex-col justify-between`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-slate-400">
                      {p.label}
                    </span>
                    <Icon className={`w-3.5 h-3.5 ${p.color}`} />
                  </div>
                  <span className="text-lg font-bold text-white">{p.count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Deadline Horizons */}
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Deadline Horizons
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {horizonItems.map((h) => {
              const Icon = h.icon;
              return (
                <div
                  key={h.label}
                  className={`px-3 py-2 rounded-lg border flex items-center justify-between ${h.badgeColor}`}
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    <span className="text-xs font-medium truncate">{h.label}</span>
                  </div>
                  <span className="text-xs font-bold shrink-0">{h.count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

