import React, { useState } from 'react';
import { X, Sliders } from 'lucide-react';
import { FocusPreference, FocusPreferenceUpdatePayload } from '../../types/focus';

interface FocusPreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: FocusPreference | null;
  onSave: (payload: FocusPreferenceUpdatePayload) => Promise<void>;
}

export const FocusPreferencesModal: React.FC<FocusPreferencesModalProps> = ({
  isOpen,
  onClose,
  preferences,
  onSave,
}) => {
  const [focusMins, setFocusMins] = useState<number>(preferences?.focus_duration_minutes ?? 25);
  const [shortBreakMins, setShortBreakMins] = useState<number>(preferences?.short_break_duration_minutes ?? 5);
  const [longBreakMins, setLongBreakMins] = useState<number>(preferences?.long_break_duration_minutes ?? 15);
  const [interval, setInterval] = useState<number>(preferences?.long_break_interval ?? 4);
  const [dailyGoalMins, setDailyGoalMins] = useState<number>(preferences?.daily_goal_minutes ?? 120);
  const [autoBreak, setAutoBreak] = useState<boolean>(preferences?.auto_start_breaks ?? false);
  const [autoFocus, setAutoFocus] = useState<boolean>(preferences?.auto_start_focus ?? false);
  const [sound, setSound] = useState<boolean>(preferences?.sound_enabled ?? true);
  const [browserNotif, setBrowserNotif] = useState<boolean>(preferences?.browser_notifications_enabled ?? true);
  const [saving, setSaving] = useState<boolean>(false);
  const [permissionState, setPermissionState] = useState<NotificationPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );

  if (!isOpen) return null;

  const handleToggleBrowserNotifications = async (checked: boolean) => {
    if (checked && typeof Notification !== 'undefined' && Notification.permission === 'default') {
      try {
        const perm = await Notification.requestPermission();
        setPermissionState(perm);
        if (perm === 'granted') {
          setBrowserNotif(true);
        } else {
          setBrowserNotif(false);
        }
      } catch {
        setBrowserNotif(false);
      }
    } else {
      setBrowserNotif(checked);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        focus_duration_minutes: focusMins,
        short_break_duration_minutes: shortBreakMins,
        long_break_duration_minutes: longBreakMins,
        long_break_interval: interval,
        daily_goal_minutes: dailyGoalMins,
        auto_start_breaks: autoBreak,
        auto_start_focus: autoFocus,
        sound_enabled: sound,
        browser_notifications_enabled: browserNotif,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-500" />
            Pomodoro Settings
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Focus (min)
              </label>
              <input
                type="number"
                min="1"
                max="120"
                value={focusMins}
                onChange={(e) => setFocusMins(parseInt(e.target.value) || 1)}
                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Short Break
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={shortBreakMins}
                onChange={(e) => setShortBreakMins(parseInt(e.target.value) || 1)}
                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Long Break
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={longBreakMins}
                onChange={(e) => setLongBreakMins(parseInt(e.target.value) || 1)}
                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Long Break Interval
              </label>
              <input
                type="number"
                min="1"
                max="12"
                value={interval}
                onChange={(e) => setInterval(parseInt(e.target.value) || 1)}
                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
              />
              <span className="text-[10px] text-gray-400">Pomodoros before long break</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Daily Goal (min)
              </label>
              <input
                type="number"
                min="5"
                max="1440"
                value={dailyGoalMins}
                onChange={(e) => setDailyGoalMins(parseInt(e.target.value) || 5)}
                className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
              />
              <span className="text-[10px] text-gray-400">Target minutes per day</span>
            </div>
          </div>

          <div className="space-y-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <label className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <span>Auto-start Breaks</span>
              <input
                type="checkbox"
                checked={autoBreak}
                onChange={(e) => setAutoBreak(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
              />
            </label>

            <label className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <span>Auto-start Next Focus</span>
              <input
                type="checkbox"
                checked={autoFocus}
                onChange={(e) => setAutoFocus(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
              />
            </label>

            <label className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <span>Notification Sound / Alerts</span>
              <input
                type="checkbox"
                checked={sound}
                onChange={(e) => setSound(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
              />
            </label>

            <label className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <div>
                <span>Desktop / Browser Notifications</span>
                {permissionState === 'denied' && (
                  <span className="block text-[11px] text-rose-500 font-medium">
                    (Blocked in browser settings)
                  </span>
                )}
              </div>
              <input
                type="checkbox"
                checked={browserNotif}
                onChange={(e) => handleToggleBrowserNotifications(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
              />
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
