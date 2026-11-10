import React, { useState, useEffect } from 'react';
import { getNotificationPreferences, updateNotificationPreferences } from '../api/notifications';
import { NotificationPreference } from '../types/notification';
import { NotificationBell } from '../components/notifications/NotificationBell';

export const NotificationPreferencesPage: React.FC = () => {
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        const data = await getNotificationPreferences();
        setPreferences(data);
      } catch {
        // Failed
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  const handleToggle = (field: keyof NotificationPreference) => {
    if (!preferences) return;
    setPreferences({
      ...preferences,
      [field]: !preferences[field],
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!preferences) return;
    setSaving(true);
    setSuccessMessage(null);
    try {
      const updated = await updateNotificationPreferences({
        in_app_enabled: preferences.in_app_enabled,
        email_enabled: preferences.email_enabled,
        task_reminders_enabled: preferences.task_reminders_enabled,
        due_date_reminders_enabled: preferences.due_date_reminders_enabled,
        overdue_reminders_enabled: preferences.overdue_reminders_enabled,
        preferred_timezone: preferences.preferred_timezone,
        quiet_hours_enabled: preferences.quiet_hours_enabled,
        quiet_hours_start: preferences.quiet_hours_start,
        quiet_hours_end: preferences.quiet_hours_end,
      });
      setPreferences(updated);
      setSuccessMessage('Notification preferences saved successfully.');
    } catch {
      // Failed
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500 text-sm">Loading preferences...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 md:p-8" data-testid="notification-preferences-page">
      <div className="max-w-3xl mx-auto space-y-6">
        <header className="flex items-center justify-between pb-6 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Notification Settings</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Customize how and when you receive reminders and alerts
            </p>
          </div>
          <NotificationBell />
        </header>

        {successMessage && (
          <div className="p-4 text-sm text-green-700 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 rounded-xl">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSave} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">Delivery Channels</h2>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">In-App Notifications</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Receive alerts in the notification center and bell dropdown</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.in_app_enabled || false}
                  onChange={() => handleToggle('in_app_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">Email Notifications</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Receive email reminders for high-priority alerts</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.email_enabled || false}
                  onChange={() => handleToggle('email_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">Notification Types</h2>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">Task Reminders</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Alerts linked directly to tasks and scheduled follow-ups</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.task_reminders_enabled || false}
                  onChange={() => handleToggle('task_reminders_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">Due Date Reminders</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Alerts when tasks approach their scheduled due date</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.due_date_reminders_enabled || false}
                  onChange={() => handleToggle('due_date_reminders_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">Overdue Reminders</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Daily digests of past-due tasks</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.overdue_reminders_enabled || false}
                  onChange={() => handleToggle('overdue_reminders_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">Quiet Hours & Timezone</h2>
            <div className="space-y-4">
              <label className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                <div>
                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">Enable Quiet Hours</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Mute non-critical notifications during designated quiet hours</div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences?.quiet_hours_enabled || false}
                  onChange={() => handleToggle('quiet_hours_enabled')}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
              </label>

              {preferences?.quiet_hours_enabled && (
                <div className="grid grid-cols-2 gap-4 pl-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Start Time</label>
                    <input
                      type="time"
                      value={preferences?.quiet_hours_start || '22:00'}
                      onChange={(e) => setPreferences({ ...preferences, quiet_hours_start: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">End Time</label>
                    <input
                      type="time"
                      value={preferences?.quiet_hours_end || '08:00'}
                      onChange={(e) => setPreferences({ ...preferences, quiet_hours_end: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-sm disabled:opacity-50 transition"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

