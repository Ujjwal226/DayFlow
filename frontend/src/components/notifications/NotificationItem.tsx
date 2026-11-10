import React from 'react';
import { Notification } from '../../types/notification';

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete,
}) => {
  const formattedTime = new Date(notification.created_at).toLocaleString();

  return (
    <div
      className={`p-3 rounded-lg border transition-all ${
        notification.is_read
          ? 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/60 opacity-75'
          : 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800'
      }`}
      data-testid={`notification-item-${notification.id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {!notification.is_read && (
              <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400 flex-shrink-0" />
            )}
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
              {notification.title}
            </h4>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 whitespace-pre-wrap">
            {notification.message}
          </p>
          <span className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 block">
            {formattedTime}
          </span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {!notification.is_read && (
            <button
              onClick={() => onMarkAsRead(notification.id)}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 font-medium px-2 py-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/40"
              title="Mark as read"
            >
              Mark Read
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(notification.id)}
              className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 p-1 rounded"
              title="Delete notification"
              aria-label="Delete notification"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

