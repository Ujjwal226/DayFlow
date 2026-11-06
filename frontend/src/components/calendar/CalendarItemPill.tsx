import React from 'react';
import { CalendarFeedItem, CalendarTaskDeadlineItem, CalendarEventItem } from '../../types/calendar';
import { CheckCircle2, Clock, Calendar as CalendarIcon, Repeat } from 'lucide-react';

interface CalendarItemPillProps {
  item: CalendarFeedItem;
  compact?: boolean;
  onClick?: (item: CalendarFeedItem) => void;
}

export const CalendarItemPill: React.FC<CalendarItemPillProps> = ({ item, compact = false, onClick }) => {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.stopPropagation();
      onClick(item);
    }
  };

  if (item.type === 'task_deadline') {
    const task = item as CalendarTaskDeadlineItem;
    const isCompleted = task.status === 'COMPLETED';
    const isOverdue = task.is_overdue;

    let priorityBadgeColor = 'border-slate-700 text-slate-300 bg-slate-800/80';
    if (task.priority === 'URGENT') priorityBadgeColor = 'border-rose-500/50 text-rose-300 bg-rose-500/10';
    else if (task.priority === 'HIGH') priorityBadgeColor = 'border-amber-500/50 text-amber-300 bg-amber-500/10';
    else if (task.priority === 'LOW') priorityBadgeColor = 'border-slate-600 text-slate-400 bg-slate-800/40';

    return (
      <div
        onClick={handleClick}
        className={`group flex items-center justify-between gap-1.5 px-2 py-1 rounded-md border text-xs transition ${
          onClick ? 'cursor-pointer hover:brightness-110' : 'cursor-default'
        } ${
          isCompleted
            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300 line-through'
            : isOverdue
            ? 'border-rose-500/40 bg-rose-500/10 text-rose-300'
            : priorityBadgeColor
        }`}
        title={`${task.title} (Deadline: ${new Date(task.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`}
      >
        <div className="flex items-center gap-1.5 min-w-0">
          <CheckCircle2 className={`w-3 h-3 flex-shrink-0 ${isCompleted ? 'text-emerald-400' : isOverdue ? 'text-rose-400' : 'text-slate-400'}`} />
          <span className="truncate font-medium">{task.title}</span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {task.recurring_task_id && (
            <span title="Recurring task occurrence">
              <Repeat className="w-2.5 h-2.5 text-indigo-400" />
            </span>
          )}
          {!compact && (
            <span className="text-[10px] text-slate-400 font-mono">
              {new Date(task.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Standalone or task-linked CalendarEvent
  const event = item as CalendarEventItem;
  const isTaskLinked = Boolean(event.task_id);
  const eventColor = event.color || (isTaskLinked ? '#6366F1' : '#3B82F6');

  return (
    <div
      onClick={handleClick}
      className={`group flex items-center justify-between gap-1.5 px-2 py-1 rounded-md border border-slate-700/60 bg-slate-800/90 text-xs text-slate-200 transition shadow-sm hover:border-slate-600 ${
        onClick ? 'cursor-pointer hover:brightness-110' : 'cursor-default'
      }`}
      style={{ borderLeftColor: eventColor, borderLeftWidth: '3px' }}
      title={`${event.title}${event.location ? ` @ ${event.location}` : ''}`}
    >
      <div className="flex items-center gap-1.5 min-w-0">
        {event.is_all_day ? (
          <CalendarIcon className="w-3 h-3 text-cyan-400 flex-shrink-0" />
        ) : (
          <Clock className="w-3 h-3 text-blue-400 flex-shrink-0" />
        )}
        <span className="truncate font-medium">{event.title}</span>
      </div>

      {!compact && !event.is_all_day && event.start_at && (
        <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">
          {new Date(event.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );
};
