import React from 'react';
import { Link } from 'react-router-dom';
import { RecurringTask } from '../../types/recurringTask';
import { RecurrenceBadge } from './RecurrenceBadge';
import { TaskPriorityBadge } from '../tasks/TaskPriorityBadge';
import { CategoryBadge } from '../categories/CategoryBadge';
import {
  Calendar,
  Layers,
  Play,
  Pause,
  Square,
  Trash2,
  Edit2,
  ExternalLink,
  Clock,
} from 'lucide-react';

interface RecurringTaskCardProps {
  series: RecurringTask;
  onEdit: (series: RecurringTask) => void;
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onStop: (id: string) => void;
  onDelete: (id: string) => void;
}

export const RecurringTaskCard: React.FC<RecurringTaskCardProps> = ({
  series,
  onEdit,
  onPause,
  onResume,
  onStop,
  onDelete,
}) => {
  const getStatusBadge = () => {
    if (series.is_stopped) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
          Stopped
        </span>
      );
    }
    if (!series.is_active) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Paused
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        Active
      </span>
    );
  };

  return (
    <div className="group rounded-2xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700 p-5 transition-all shadow-sm flex flex-col justify-between">
      <div>
        {/* Top badges */}
        <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <RecurrenceBadge frequency={series.frequency} interval={series.interval} />
            <TaskPriorityBadge priority={series.priority} />
            {series.category && <CategoryBadge category={series.category} />}
          </div>
          <div>{getStatusBadge()}</div>
        </div>

        {/* Title */}
        <Link
          to={`/recurring-tasks/${series.id}`}
          className="text-base font-bold text-white hover:text-emerald-400 transition flex items-center gap-1.5 line-clamp-1"
        >
          <span>{series.title}</span>
          <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition shrink-0 text-slate-400" />
        </Link>

        {/* Description */}
        {series.description && (
          <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
            {series.description}
          </p>
        )}

        {/* Schedule metadata */}
        <div className="mt-4 pt-3 border-t border-slate-800/60 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span>
              Next:{' '}
              <strong className="text-slate-300 font-semibold">
                {series.next_occurrence_date || 'None'}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span>
              Generated:{' '}
              <strong className="text-slate-300 font-semibold">
                {series.occurrences_generated}
                {series.max_occurrences ? ` / ${series.max_occurrences}` : ''}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 col-span-2 text-slate-500">
            <Clock className="w-3.5 h-3.5 shrink-0" />
            <span>
              Started {series.start_date}
              {series.end_date ? ` · Ends ${series.end_date}` : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {!series.is_stopped && (
            <>
              {series.is_active ? (
                <button
                  type="button"
                  onClick={() => onPause(series.id)}
                  title="Pause recurring schedule"
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium transition flex items-center gap-1 border border-slate-700"
                >
                  <Pause className="w-3 h-3 text-amber-400" />
                  <span>Pause</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => onResume(series.id)}
                  title="Resume recurring schedule"
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-medium transition flex items-center gap-1 border border-emerald-500/30"
                >
                  <Play className="w-3 h-3" />
                  <span>Resume</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => onStop(series.id)}
                title="Stop recurrence permanently"
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 text-xs font-medium transition flex items-center gap-1 border border-slate-700"
              >
                <Square className="w-3 h-3" />
                <span>Stop</span>
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onEdit(series)}
            title="Edit series configuration"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => onDelete(series.id)}
            title="Delete recurring series"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

