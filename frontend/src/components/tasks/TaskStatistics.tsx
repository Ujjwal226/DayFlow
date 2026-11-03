import React from 'react';
import { TaskStatistics } from '../../types/task';
import {
  CheckCircle2,
  Clock,
  CircleDot,
  AlertTriangle,
  Calendar,
  Layers,
} from 'lucide-react';

interface TaskStatisticsProps {
  stats: TaskStatistics | null;
  isLoading?: boolean;
}

export const TaskStatisticsCard: React.FC<TaskStatisticsProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="h-20 bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse"
          />
        ))}
      </div>
    );
  }

  const items = [
    {
      label: 'Total Active',
      value: stats.total,
      icon: Layers,
      color: 'text-slate-200',
      bg: 'bg-slate-800/40 border-slate-700/60',
    },
    {
      label: 'To Do',
      value: stats.todo,
      icon: CircleDot,
      color: 'text-slate-300',
      bg: 'bg-slate-800/40 border-slate-700/60',
    },
    {
      label: 'In Progress',
      value: stats.in_progress,
      icon: Clock,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20',
    },
    {
      label: 'Completed',
      value: stats.completed,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'Overdue',
      value: stats.overdue,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20',
    },
    {
      label: 'Upcoming',
      value: stats.upcoming,
      icon: Calendar,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className={`p-3.5 rounded-2xl border ${item.bg} flex flex-col justify-between transition hover:scale-[1.02]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">{item.label}</span>
              <Icon className={`w-3.5 h-3.5 ${item.color}`} />
            </div>
            <div className={`text-xl font-bold mt-2 ${item.color}`}>{item.value}</div>
          </div>
        );
      })}
    </div>
  );
};

