import React, { useState } from 'react';
import { Reminder } from '../../types/reminder';

interface ReminderCardProps {
  reminder: Reminder;
  onEdit: (reminder: Reminder) => void;
  onDelete: (id: string) => void;
  onComplete: (id: string) => void;
  onDismiss: (id: string) => void;
  onSnooze: (id: string, minutes: number) => void;
}

export const ReminderCard: React.FC<ReminderCardProps> = ({
  reminder,
  onEdit,
  onDelete,
  onComplete,
  onDismiss,
  onSnooze,
}) => {
  const [showSnoozeMenu, setShowSnoozeMenu] = useState(false);

  const getStatusBadge = () => {
    switch (reminder.status) {
      case 'PENDING':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">Pending</span>;
      case 'SNOOZED':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">Snoozed</span>;
      case 'SENT':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">Sent</span>;
      case 'COMPLETED':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">Completed</span>;
      case 'DISMISSED':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">Dismissed</span>;
      default:
        return null;
    }
  };

  const formattedDate = new Date(reminder.scheduled_at).toLocaleString();
  const snoozedDate = reminder.snoozed_until ? new Date(reminder.snoozed_until).toLocaleString() : null;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm hover:shadow transition" data-testid={`reminder-card-${reminder.id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base truncate">
              {reminder.title}
            </h3>
            {getStatusBadge()}
            {reminder.recurrence !== 'NONE' && (
              <span className="px-2 py-0.5 text-[11px] font-medium rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300">
                ↻ {reminder.recurrence.toLowerCase()}
              </span>
            )}
          </div>

          {reminder.description && (
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 whitespace-pre-wrap">
              {reminder.description}
            </p>
          )}

          <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 mt-3 flex-wrap">
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Scheduled: {formattedDate}
            </span>

            {snoozedDate && reminder.status === 'SNOOZED' && (
              <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400 font-medium">
                Snoozed until: {snoozedDate}
              </span>
            )}

            <span className="flex items-center gap-1">
              Channels: {reminder.delivery_channels}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 relative">
          <button
            onClick={() => onEdit(reminder)}
            className="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            title="Edit reminder"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>

          <button
            onClick={() => onDelete(reminder.id)}
            className="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            title="Delete reminder"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          {reminder.status !== 'COMPLETED' && (
            <button
              onClick={() => onComplete(reminder.id)}
              className="px-3 py-1 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 dark:bg-green-950/40 dark:text-green-300 rounded-lg transition"
            >
              Complete
            </button>
          )}

          {reminder.status !== 'DISMISSED' && reminder.status !== 'COMPLETED' && (
            <button
              onClick={() => onDismiss(reminder.id)}
              className="px-3 py-1 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 rounded-lg transition"
            >
              Dismiss
            </button>
          )}
        </div>

        {reminder.status !== 'COMPLETED' && (
          <div className="relative">
            <button
              onClick={() => setShowSnoozeMenu(!showSnoozeMenu)}
              className="px-3 py-1 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/40 dark:text-purple-300 rounded-lg transition"
            >
              Snooze ▾
            </button>

            {showSnoozeMenu && (
              <div className="absolute right-0 bottom-full mb-1 w-32 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg py-1 z-10">
                <button
                  onClick={() => {
                    onSnooze(reminder.id, 15);
                    setShowSnoozeMenu(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  15 minutes
                </button>
                <button
                  onClick={() => {
                    onSnooze(reminder.id, 60);
                    setShowSnoozeMenu(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  1 hour
                </button>
                <button
                  onClick={() => {
                    onSnooze(reminder.id, 1440);
                    setShowSnoozeMenu(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  1 day
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

