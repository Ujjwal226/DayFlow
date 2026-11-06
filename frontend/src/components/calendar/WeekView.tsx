import React from 'react';
import { CalendarFeedItem, CalendarEventItem } from '../../types/calendar';
import { CalendarItemPill } from './CalendarItemPill';

interface WeekViewProps {
  currentDate: Date;
  items: CalendarFeedItem[];
  onSelectDate: (date: Date) => void;
  onSlotClick?: (date: Date) => void;
  onItemClick?: (item: CalendarFeedItem) => void;
}

export const WeekView: React.FC<WeekViewProps> = ({
  currentDate,
  items,
  onSelectDate,
  onSlotClick,
  onItemClick,
}) => {
  const d = new Date(currentDate);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d.setDate(diff));

  const weekDays: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const dayDate = new Date(monday);
    dayDate.setDate(monday.getDate() + i);
    weekDays.push(dayDate);
  }

  const today = new Date();
  const isToday = (date: Date) =>
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear();

  const hours = Array.from({ length: 24 }, (_, i) => i);

  const getDayItems = (dayDate: Date) => {
    const dayStart = new Date(dayDate.getFullYear(), dayDate.getMonth(), dayDate.getDate(), 0, 0, 0);
    const dayEnd = new Date(dayDate.getFullYear(), dayDate.getMonth(), dayDate.getDate() + 1, 0, 0, 0);

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
          if (dayDate >= evStart && dayDate < evEnd) {
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

    return { allDayOrDeadlines, timedEvents };
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur flex flex-col">
      {/* Week Header */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-slate-800 bg-slate-800/40 divide-x divide-slate-800 text-center">
        <div className="p-3 text-xs text-slate-500 font-semibold uppercase">GMT</div>
        {weekDays.map((date, idx) => {
          const dayIsToday = isToday(date);
          return (
            <div
              key={idx}
              onClick={() => onSelectDate(date)}
              className="p-3 cursor-pointer hover:bg-slate-800/60 transition group"
            >
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {date.toLocaleDateString(undefined, { weekday: 'short' })}
              </div>
              <div
                className={`text-sm font-bold mt-1 inline-flex items-center justify-center w-7 h-7 rounded-full ${
                  dayIsToday
                    ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30'
                    : 'text-slate-200 group-hover:text-white'
                }`}
              >
                {date.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* All-Day and Deadlines Row */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-slate-800 bg-slate-900/40 divide-x divide-slate-800">
        <div className="p-2 text-[10px] text-slate-400 font-semibold uppercase tracking-wider text-center flex items-center justify-center">
          All-Day / Due
        </div>
        {weekDays.map((date, idx) => {
          const { allDayOrDeadlines } = getDayItems(date);
          return (
            <div
              key={idx}
              onClick={() => onSlotClick && onSlotClick(date)}
              className="p-1.5 min-h-[44px] space-y-1 cursor-pointer hover:bg-slate-800/20"
            >
              {allDayOrDeadlines.map((item) => (
                <CalendarItemPill
                  key={item.id}
                  item={item}
                  compact
                  onClick={onItemClick}
                />
              ))}
            </div>
          );
        })}
      </div>

      {/* Hourly Timed Grid */}
      <div className="overflow-y-auto max-h-[600px] divide-y divide-slate-800/60">
        {hours.map((hour) => (
          <div key={hour} className="grid grid-cols-[60px_repeat(7,1fr)] divide-x divide-slate-800/60 min-h-[50px]">
            {/* Hour Label */}
            <div className="pr-2 pt-1 text-[11px] text-slate-500 font-mono text-right">
              {hour.toString().padStart(2, '0')}:00
            </div>

            {/* 7 Columns for the hour */}
            {weekDays.map((date, dayIdx) => {
              const { timedEvents } = getDayItems(date);
              const eventsInHour = timedEvents.filter((ev) => {
                if (!ev.start_at) return false;
                const startHour = new Date(ev.start_at).getHours();
                return startHour === hour;
              });

              return (
                <div
                  key={dayIdx}
                  onClick={() => {
                    if (onSlotClick) {
                      const slotDate = new Date(date);
                      slotDate.setHours(hour, 0, 0, 0);
                      onSlotClick(slotDate);
                    }
                  }}
                  className="p-1 space-y-1 relative group hover:bg-slate-800/30 transition cursor-pointer"
                >
                  {eventsInHour.map((ev) => (
                    <CalendarItemPill
                      key={ev.id}
                      item={ev}
                      compact
                      onClick={onItemClick}
                    />
                  ))}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};
