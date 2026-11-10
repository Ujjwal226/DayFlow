import React, { useState, useEffect, useCallback } from 'react';
import { Settings, RefreshCw, History } from 'lucide-react';
import { focusApi } from '../api/focus';
import { tasksApi } from '../api/tasks';
import {
  FocusSessionActiveResponse,
  FocusPreference,
  FocusAnalyticsOverview,
  FocusSession,
  FocusSessionType,
  FocusPreferenceUpdatePayload,
} from '../types/focus';
import { Task } from '../types/task';
import { PomodoroTimer } from '../components/focus/PomodoroTimer';
import { FocusAnalyticsCard } from '../components/focus/FocusAnalyticsCard';
import { FocusPreferencesModal } from '../components/focus/FocusPreferencesModal';

export const FocusPage: React.FC = () => {
  const [activeSession, setActiveSession] = useState<FocusSessionActiveResponse | null>(null);
  const [preferences, setPreferences] = useState<FocusPreference | null>(null);
  const [analytics, setAnalytics] = useState<FocusAnalyticsOverview | null>(null);
  const [history, setHistory] = useState<FocusSession[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [activeRes, prefRes, anRes, histRes, taskRes] = await Promise.all([
        focusApi.getActiveSession(),
        focusApi.getPreferences(),
        focusApi.getAnalytics(),
        focusApi.getSessionHistory(15),
        tasksApi.listTasks({ page_size: 100 }),
      ]);

      setActiveSession(activeRes);
      setPreferences(prefRes);
      setAnalytics(anRes);
      setHistory(histRes);
      setTasks(taskRes.items);

      if (activeRes?.session.task_id) {
        setSelectedTaskId(activeRes.session.task_id);
      }
    } catch (err: unknown) {
      console.error('Failed to load focus state:', err);
      setError('Failed to load focus data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStart = async (type: FocusSessionType, plannedSeconds: number, taskId?: string | null) => {
    try {
      setIsLoading(true);
      setError(null);
      const session = await focusApi.startSession({
        session_type: type,
        planned_duration_seconds: plannedSeconds,
        task_id: taskId,
      });
      setActiveSession(session);
      // Reload analytics & history
      const [anRes, histRes] = await Promise.all([
        focusApi.getAnalytics(),
        focusApi.getSessionHistory(15),
      ]);
      setAnalytics(anRes);
      setHistory(histRes);
    } catch (err: unknown) {
      console.error('Error starting session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to start session');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePause = async () => {
    if (!activeSession) return;
    try {
      setIsLoading(true);
      setError(null);
      const updated = await focusApi.pauseSession(activeSession.session.id);
      setActiveSession(updated);
    } catch (err: unknown) {
      console.error('Error pausing session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to pause session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResume = async () => {
    if (!activeSession) return;
    try {
      setIsLoading(true);
      setError(null);
      const updated = await focusApi.resumeSession(activeSession.session.id);
      setActiveSession(updated);
    } catch (err: unknown) {
      console.error('Error resuming session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to resume session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!activeSession) return;
    try {
      setIsLoading(true);
      setError(null);
      await focusApi.completeSession(activeSession.session.id);
      setActiveSession(null);
      // Refresh analytics and history
      const [anRes, histRes] = await Promise.all([
        focusApi.getAnalytics(),
        focusApi.getSessionHistory(15),
      ]);
      setAnalytics(anRes);
      setHistory(histRes);
    } catch (err: unknown) {
      console.error('Error completing session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to complete session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAbandon = async () => {
    if (!activeSession) return;
    try {
      setIsLoading(true);
      setError(null);
      await focusApi.abandonSession(activeSession.session.id);
      setActiveSession(null);
      // Refresh analytics and history
      const [anRes, histRes] = await Promise.all([
        focusApi.getAnalytics(),
        focusApi.getSessionHistory(15),
      ]);
      setAnalytics(anRes);
      setHistory(histRes);
    } catch (err: unknown) {
      console.error('Error abandoning session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to abandon session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!activeSession) return;
    try {
      setIsLoading(true);
      setError(null);
      const transitioned = await focusApi.skipSession(activeSession.session.id);
      setActiveSession(transitioned);
      // Refresh analytics and history
      const [anRes, histRes] = await Promise.all([
        focusApi.getAnalytics(),
        focusApi.getSessionHistory(15),
      ]);
      setAnalytics(anRes);
      setHistory(histRes);
    } catch (err: unknown) {
      console.error('Error skipping session:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to skip session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSavePreferences = async (payload: FocusPreferenceUpdatePayload) => {
    try {
      const updated = await focusApi.updatePreferences(payload);
      setPreferences(updated);
      const anRes = await focusApi.getAnalytics();
      setAnalytics(anRes);
    } catch (err: unknown) {
      console.error('Error updating preferences:', err);
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to update preferences');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200 dark:border-gray-800">
        <div>
          <h1 className="text-2xl font-black text-gray-900 dark:text-white flex items-center gap-2">
            Focus & Pomodoro
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Deep work timer with task linking and daily streak goals.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData()}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-xl font-medium text-sm transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 rounded-xl text-rose-700 dark:text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Main Grid: Timer on Left, Analytics on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-6">
          <PomodoroTimer
            activeSession={activeSession}
            preferences={preferences}
            tasks={tasks}
            selectedTaskId={selectedTaskId}
            onSelectTask={setSelectedTaskId}
            onStart={handleStart}
            onPause={handlePause}
            onResume={handleResume}
            onComplete={handleComplete}
            onAbandon={handleAbandon}
            onSkip={handleSkip}
            isLoading={isLoading}
          />
        </div>

        <div className="lg:col-span-6 space-y-6">
          <FocusAnalyticsCard analytics={analytics} />
        </div>
      </div>

      {/* Recent Session History */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-md font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-indigo-500" />
          Recent Sessions
        </h3>

        {history.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">
            No focus sessions recorded yet. Start a session to build your deep work streak!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-700 text-gray-400 font-semibold uppercase">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Linked Task</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/60 font-medium">
                {history.map((s) => {
                  const mins = Math.round(s.actual_duration_seconds / 60);
                  return (
                    <tr key={s.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                      <td className="py-3 px-3 text-gray-600 dark:text-gray-300">
                        {new Date(s.started_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            s.session_type === 'FOCUS'
                              ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400'
                              : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400'
                          }`}
                        >
                          {s.session_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-gray-800 dark:text-gray-200 max-w-[200px] truncate">
                        {s.task_title || '-'}
                      </td>
                      <td className="py-3 px-3 text-gray-700 dark:text-gray-300">
                        {mins} min
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                            s.status === 'COMPLETED'
                              ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-400'
                              : s.status === 'ABANDONED'
                              ? 'text-rose-600 bg-rose-50 dark:bg-rose-950/40 dark:text-rose-400'
                              : 'text-amber-600 bg-amber-50 dark:bg-amber-950/40 dark:text-amber-400'
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <FocusPreferencesModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        preferences={preferences}
        onSave={handleSavePreferences}
      />
    </div>
  );
};
