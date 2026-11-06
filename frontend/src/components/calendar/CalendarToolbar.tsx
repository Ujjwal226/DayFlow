import React from 'react';
import { CalendarViewMode } from '../../types/calendar';
import { ChevronLeft, ChevronRight, Grid, List, Columns, Plus, Clock, Filter } from 'lucide-react';

interface CalendarToolbarProps {
  currentDate: Date;
  viewMode: CalendarViewMode;
  onViewModeChange: (mode: CalendarViewMode) => void;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
  onNewEvent: () => void;
  onScheduleTask: () => void;
  onOpenFilters: () => void;
  activeFilterCount: number;
}

export const CalendarToolbar: React.FC<CalendarToolbarProps> = ({
  currentDate,
  viewMode,
  onViewModeChange,
  onPrev,
  onNext,
  onToday,
  onNewEvent,
  onScheduleTask,
  onOpenFilters,
  activeFilterCount,
}) => {
  const getPeriodLabel = (): string => {
    const year = currentDate.getFullYear();
    const monthName = currentDate.toLocaleString('default', { month: 'long' });

    if (viewMode === 'month') {
      return `${monthName} ${year}`;
    }

    if (viewMode === 'week') {
      const d = new Date(currentDate);
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const monday = new Date(d.setDate(diff));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      const monMonth = monday.toLocaleString('default', { month: 'short' });
      const sunMonth = sunday.toLocaleString('default', { month: 'short' });

      if (monMonth === sunMonth) {
        return `${monMonth} ${monday.getDate()} – ${sunday.getDate()}, ${year}`;
      }
      return `${monMonth} ${monday.getDate()} – ${sunMonth} ${sunday.getDate()}, ${year}`;
    }

    return currentDate.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-2xl backdrop-blur">
      {/* Date navigation controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToday}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition shadow-sm hover:text-white"
          title="Jump to today"
        >
          Today
        </button>

        <div className="flex items-center rounded-xl bg-slate-800/80 border border-slate-700 p-0.5">
          <button
            onClick={onPrev}
            className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-300 hover:text-white transition"
            aria-label="Previous period"
            title="Previous period"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={onNext}
            className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-300 hover:text-white transition"
            aria-label="Next period"
            title="Next period"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <h2 className="text-base sm:text-lg font-bold text-white tracking-tight ml-2">
          {getPeriodLabel()}
        </h2>
      </div>

      {/* Action buttons & View toggles */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Interactive Action Buttons */}
        <button
          onClick={onNewEvent}
          className="px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow-sm shadow-emerald-500/20"
          title="Create a new calendar event"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Event</span>
        </button>

        <button
          onClick={onScheduleTask}
          className="px-3 py-1.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition flex items-center gap-1.5"
          title="Schedule task into calendar time block"
        >
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <span>Schedule Task</span>
        </button>

        {/* Filters button with badge */}
        <button
          onClick={onOpenFilters}
          className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition flex items-center gap-1.5 ${
            activeFilterCount > 0
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300 hover:text-white'
          }`}
          title="Open calendar filters"
        >
          <Filter className="w-3.5 h-3.5" />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-bold flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>

        {/* View mode toggle switch */}
        <div className="flex items-center rounded-xl bg-slate-800/90 border border-slate-700 p-1">
          <button
            onClick={() => onViewModeChange('month')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition ${
              viewMode === 'month'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
            aria-pressed={viewMode === 'month'}
          >
            <Grid className="w-3.5 h-3.5" />
            <span>Month</span>
          </button>

          <button
            onClick={() => onViewModeChange('week')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition ${
              viewMode === 'week'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
            aria-pressed={viewMode === 'week'}
          >
            <Columns className="w-3.5 h-3.5" />
            <span>Week</span>
          </button>

          <button
            onClick={() => onViewModeChange('day')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition ${
              viewMode === 'day'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
            aria-pressed={viewMode === 'day'}
          >
            <List className="w-3.5 h-3.5" />
            <span>Day</span>
          </button>
        </div>
      </div>
    </div>
  );
};
