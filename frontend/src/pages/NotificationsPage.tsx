import React, { useState, useEffect } from 'react';
import { getNotifications, markNotificationAsRead, markAllNotificationsAsRead, deleteNotification } from '../api/notifications';
import { Notification } from '../types/notification';
import { NotificationItem } from '../components/notifications/NotificationItem';
import { NotificationBell } from '../components/notifications/NotificationBell';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadFilter, setUnreadFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const isRead = unreadFilter === 'unread' ? false : unreadFilter === 'read' ? true : undefined;
      const data = await getNotifications(isRead, 100, 0);
      setNotifications(data);
    } catch {
      // Failed to load
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unreadFilter]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
    } catch {
      // Failed
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
    } catch {
      // Failed
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch {
      // Failed
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 md:p-8" data-testid="notifications-page">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Notifications</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              View your notification history, reminders, and alerts
            </p>
          </div>

          <div className="flex items-center gap-3">
            <NotificationBell />
            <button
              onClick={handleMarkAllRead}
              className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm transition"
            >
              Mark all read
            </button>
          </div>
        </header>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadFilter('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
              unreadFilter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setUnreadFilter('unread')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
              unreadFilter === 'unread'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => setUnreadFilter('read')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition ${
              unreadFilter === 'read'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'
            }`}
          >
            Read
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
            <p className="text-slate-500 dark:text-slate-400 text-sm">No notifications found.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((item) => (
              <NotificationItem
                key={item.id}
                notification={item}
                onMarkAsRead={handleMarkAsRead}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
