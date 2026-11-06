import React from 'react';
import { CalendarFeedItem, CalendarEventItem } from '../../types/calendar';
import { CalendarItemPill } from './CalendarItemPill';
import { Plus } from 'lucide-react';

interface MonthViewProps {
  currentDate: Date;
  items: CalendarFeedItem[];
  onSelectDate: (date: Date) => void;
  onSlotClick?: (date: Date) => void;
  onItemClick?: (item: CalendarFeedItem) => void;
}

export const MonthView: React.FC<MonthViewProps> = ({
  currentDate,
  items,
  onSelectDate,
  onSlotClick,
  onItemClick,
}) => {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  let startingDayOfWeek = firstDayOfMonth.getDay() - 1;
  if (startingDayOfWeek === -1) startingDayOfWeek = 6;

  const daysInMonth = lastDayOfMonth.getDate();
  const calendarCells: { date: Date; isCurrentMonth: boolean }[] = [];

  const prevMonthLastDay = new Date(year, month, 0).getDate();
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    calendarCells.push({
      date: new Date(year, month - 1, prevMonthLastDay - i),
      isCurrentMonth: false,
    });
  }

  for (let day = 1; day <= daysInMonth; day++) {
    calendarCells.push({
      date: new Date(year, month, day),
      isCurrentMonth: true,
    });
  }

  const remainingCells = (7 - (calendarCells.length % 7)) % 7;
  for (let day = 1; day <= remainingCells; day++) {
    calendarCells.push({
      date: new Date(year, month + 1, day),
      isCurrentMonth: false,
    });
  }

  const today = new Date();
  const isToday = (d: Date) =>
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear();

  const isSelected = (d: Date) =>
    d.getDate() === currentDate.getDate() &&
    d.getMonth() === currentDate.getMonth() &&
    d.getFullYear() === currentDate.getFullYear();

  const getItemsForDay = (cellDate: Date): CalendarFeedItem[] => {
    const cellStart = new Date(cellDate.getFullYear(), cellDate.getMonth(), cellDate.getDate(), 0, 0, 0);
    const cellEnd = new Date(cellDate.getFullYear(), cellDate.getMonth(), cellDate.getDate() + 1, 0, 0, 0);

    return items.filter((item) => {
      if (item.type === 'task_deadline') {
        const due = new Date(item.due_date);
        return due >= cellStart && due < cellEnd;
      }

      const ev = item as CalendarEventItem;
      if (ev.is_all_day && ev.start_date && ev.end_date) {
        const [sYear, sMonth, sDay] = ev.start_date.split('-').map(Number);
        const [eYear, eMonth, eDay] = ev.end_date.split('-').map(Number);
        const evStart = new Date(sYear, sMonth - 1, sDay);
        const evEnd = new Date(eYear, eMonth - 1, eDay);
        return cellDate >= evStart && cellDate < evEnd;
      }

      if (ev.start_at && ev.end_at) {
        const evStart = new Date(ev.start_at);
        const evEnd = new Date(ev.end_at);
        return evStart < cellEnd && evEnd > cellStart;
      }

      return false;
    });
  };

  const weekdayHeaders = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur">
      <div className="grid grid-cols-7 border-b border-slate-800 bg-slate-800/40 text-center py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
        {weekdayHeaders.map((day) => (
          <div key={day}>{day}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 auto-rows-fr divide-x divide-y divide-slate-800 border-b border-slate-800">
        {calendarCells.map((cell, idx) => {
          const dayItems = getItemsForDay(cell.date);
          const cellIsToday = isToday(cell.date);
          const cellIsSelected = isSelected(cell.date);

          return (
            <div
              key={idx}
              onClick={() => onSelectDate(cell.date)}
              className={`min-h-[110px] p-2 flex flex-col justify-between transition cursor-pointer group relative ${
                !cell.isCurrentMonth
                  ? 'bg-slate-950/40 text-slate-600'
                  : 'bg-slate-900/20 text-slate-300 hover:bg-slate-800/30'
              } ${cellIsSelected ? 'ring-1 ring-emerald-500/50 bg-emerald-500/5' : ''}`}
            >
              {/* Day header */}
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center transition ${
                    cellIsToday
                      ? 'bg-emerald-500 text-white font-extrabold shadow-sm shadow-emerald-500/40'
                      : cellIsSelected
                      ? 'bg-slate-800 text-emerald-400 font-semibold'
                      : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                >
                  {cell.date.getDate()}
                </span>

                <div className="flex items-center gap-1">
                  {onSlotClick && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSlotClick(cell.date);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition"
                      title="Add event on this day"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {dayItems.length > 0 && (
                    <span className="text-[10px] font-mono text-slate-500">
                      {dayItems.length}
                    </span>
                  )}
                </div>
              </div>

              {/* Day items list */}
              <div className="flex-1 space-y-1 overflow-hidden">
                {dayItems.slice(0, 3).map((item) => (
                  <CalendarItemPill
                    key={item.id}
                    item={item}
                    compact
                    onClick={onItemClick}
                  />
                ))}

                {dayItems.length > 3 && (
                  <div className="text-[10px] text-emerald-400 font-semibold px-1 py-0.5 hover:underline">
                    +{dayItems.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
