import React, { useState, useEffect } from 'react';
import { getReminders, createReminder, updateReminder, deleteReminder, completeReminder, dismissReminder, snoozeReminder } from '../api/reminders';
import { tasksApi } from '../api/tasks';
import { Reminder, ReminderCreatePayload, ReminderUpdatePayload } from '../types/reminder';
import { ReminderCard } from '../components/reminders/ReminderCard';
import { ReminderModal } from '../components/reminders/ReminderModal';
import { NotificationBell } from '../components/notifications/NotificationBell';

export const RemindersPage: React.FC = () => {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [tasks, setTasks] = useState<Array<{ id: string; title: string }>>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rems, taskListResp] = await Promise.all([
        getReminders(statusFilter || undefined),
        tasksApi.listTasks().catch(() => ({ items: [] })),
      ]);
      setReminders(rems);
      setTasks(Array.isArray(taskListResp?.items) ? taskListResp.items : []);
    } catch {
      // Failed to load
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleSave = async (payload: ReminderCreatePayload | ReminderUpdatePayload) => {
    if (editingReminder) {
      const updated = await updateReminder(editingReminder.id, payload as ReminderUpdatePayload);
      setReminders((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } else {
      const created = await createReminder(payload as ReminderCreatePayload);
      setReminders((prev) => [created, ...prev]);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this reminder?')) return;
    try {
      await deleteReminder(id);
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch {
      // Handle error
    }
  };

  const handleComplete = async (id: string) => {
    try {
      const updated = await completeReminder(id);
      setReminders((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch {
      // Error
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      const updated = await dismissReminder(id);
      setReminders((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch {
      // Error
    }
  };

  const handleSnooze = async (id: string, minutes: number) => {
    try {
      const updated = await snoozeReminder(id, { snooze_minutes: minutes });
      setReminders((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch {
      // Error
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 md:p-8" data-testid="reminders-page">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Reminders</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage your personal and task-linked alerts and notifications
            </p>
          </div>

          <div className="flex items-center gap-3">
            <NotificationBell />
            <button
              onClick={() => {
                setEditingReminder(null);
                setIsModalOpen(true);
              }}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition flex items-center gap-2"
            >
              <span>+</span> New Reminder
            </button>
          </div>
        </header>

        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-500 uppercase">Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Reminders</option>
              <option value="PENDING">Pending</option>
              <option value="SNOOZED">Snoozed</option>
              <option value="SENT">Sent</option>
              <option value="COMPLETED">Completed</option>
              <option value="DISMISSED">Dismissed</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">Loading reminders...</div>
        ) : reminders.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
            <p className="text-slate-500 dark:text-slate-400 text-sm">No reminders found.</p>
            <button
              onClick={() => {
                setEditingReminder(null);
                setIsModalOpen(true);
              }}
              className="mt-4 px-4 py-2 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
            >
              Create your first reminder
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reminders.map((rem) => (
              <ReminderCard
                key={rem.id}
                reminder={rem}
                onEdit={(r) => {
                  setEditingReminder(r);
                  setIsModalOpen(true);
                }}
                onDelete={handleDelete}
                onComplete={handleComplete}
                onDismiss={handleDismiss}
                onSnooze={handleSnooze}
              />
            ))}
          </div>
        )}

        <ReminderModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setEditingReminder(null);
          }}
          onSave={handleSave}
          initialData={editingReminder}
          tasks={tasks}
        />
      </div>
    </div>
  );
};
