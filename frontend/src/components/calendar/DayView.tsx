import React from 'react';
import { CalendarFeedItem, CalendarEventItem } from '../../types/calendar';
import { CalendarItemPill } from './CalendarItemPill';
import { Calendar as CalendarIcon, Clock, CheckCircle2 } from 'lucide-react';

interface DayViewProps {
  currentDate: Date;
  items: CalendarFeedItem[];
  onSlotClick?: (date: Date) => void;
  onItemClick?: (item: CalendarFeedItem) => void;
}

export const DayView: React.FC<DayViewProps> = ({
  currentDate,
  items,
  onSlotClick,
  onItemClick,
}) => {
  const dayStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 0, 0, 0);
  const dayEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate() + 1, 0, 0, 0);

  const allDayOrDeadlines: CalendarFeedItem[] = [];
  const timedEvents: CalendarEventItem[] = [];

  items.forEach((item) => {
    if (item.type === 'task_deadline') {
      const due = new Date(item.due_date);
      if (due >= dayStart && due < dayEnd) {
        allDayOrDeadlines.push(item);
      }
    } else {
      const ev = item as CalendarEventItem;
      if (ev.is_all_day && ev.start_date && ev.end_date) {
        const [sYear, sMonth, sDay] = ev.start_date.split('-').map(Number);
        const [eYear, eMonth, eDay] = ev.end_date.split('-').map(Number);
        const evStart = new Date(sYear, sMonth - 1, sDay);
        const evEnd = new Date(eYear, eMonth - 1, eDay);
        if (currentDate >= evStart && currentDate < evEnd) {
          allDayOrDeadlines.push(item);
        }
      } else if (ev.start_at && ev.end_at) {
        const evStart = new Date(ev.start_at);
        const evEnd = new Date(ev.end_at);
        if (evStart < dayEnd && evEnd > dayStart) {
          timedEvents.push(ev);
        }
      }
    }
  });

  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur flex flex-col">
      {/* Day Banner */}
      <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            {currentDate.toLocaleDateString(undefined, { weekday: 'long' })}
          </span>
          <h3 className="text-xl font-extrabold text-white">
            {currentDate.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{allDayOrDeadlines.length} All-Day / Tasks</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>{timedEvents.length} Scheduled Blocks</span>
          </div>
        </div>
      </div>

      {/* All-Day & Deadlines Section */}
      {allDayOrDeadlines.length > 0 && (
        <div className="p-3 border-b border-slate-800 bg-slate-900/30 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider w-36 flex-shrink-0">
            <CalendarIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>All-Day / Due</span>
          </div>
          <div className="flex-1 flex flex-wrap gap-2">
            {allDayOrDeadlines.map((item) => (
              <div key={item.id} className="min-w-[200px]">
                <CalendarItemPill item={item} onClick={onItemClick} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hourly Timeline */}
      <div className="overflow-y-auto max-h-[600px] divide-y divide-slate-800/60">
        {hours.map((hour) => {
          const eventsInHour = timedEvents.filter((ev) => {
            if (!ev.start_at) return false;
            const startHour = new Date(ev.start_at).getHours();
            return startHour === hour;
          });

          return (
            <div
              key={hour}
              onClick={() => {
                if (onSlotClick) {
                  const slotDate = new Date(currentDate);
                  slotDate.setHours(hour, 0, 0, 0);
                  onSlotClick(slotDate);
                }
              }}
              className="grid grid-cols-[70px_1fr] divide-x divide-slate-800/60 min-h-[55px] cursor-pointer hover:bg-slate-800/20 transition"
            >
              {/* Hour Label */}
              <div className="pr-3 pt-2 text-xs text-slate-500 font-mono text-right">
                {hour.toString().padStart(2, '0')}:00
              </div>

              {/* Slot content */}
              <div className="p-2 space-y-2">
                {eventsInHour.map((ev) => (
                  <div key={ev.id} className="max-w-md">
                    <CalendarItemPill item={ev} onClick={onItemClick} />
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
