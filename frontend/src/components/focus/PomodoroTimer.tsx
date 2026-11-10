import React, { useEffect, useState, useMemo } from 'react';
import { Play, Pause, Square, CheckCircle2, SkipForward } from 'lucide-react';
import { FocusSessionActiveResponse, FocusSessionType, FocusPreference } from '../../types/focus';
import { Task } from '../../types/task';

interface PomodoroTimerProps {
  activeSession: FocusSessionActiveResponse | null;
  preferences: FocusPreference | null;
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string | null) => void;
  onStart: (type: FocusSessionType, plannedSeconds: number, taskId?: string | null) => Promise<void>;
  onPause: () => Promise<void>;
  onResume: () => Promise<void>;
  onComplete: () => Promise<void>;
  onAbandon: () => Promise<void>;
  onSkip: () => Promise<void>;
  isLoading: boolean;
}

export const PomodoroTimer: React.FC<PomodoroTimerProps> = ({
  activeSession,
  preferences,
  tasks,
  selectedTaskId,
  onSelectTask,
  onStart,
  onPause,
  onResume,
  onComplete,
  onAbandon,
  onSkip,
  isLoading,
}) => {
  const [targetType, setTargetType] = useState<FocusSessionType>('FOCUS');
  const [displaySeconds, setDisplaySeconds] = useState<number>(25 * 60);

  // Default durations based on preferences
  const defaultDurations = useMemo(() => {
    return {
      FOCUS: (preferences?.focus_duration_minutes ?? 25) * 60,
      SHORT_BREAK: (preferences?.short_break_duration_minutes ?? 5) * 60,
      LONG_BREAK: (preferences?.long_break_duration_minutes ?? 15) * 60,
    };
  }, [preferences]);

  // Client-side ticker synchronized with authoritative backend timestamps
  useEffect(() => {
    if (!activeSession) {
      setDisplaySeconds(defaultDurations[targetType]);
      return;
    }

    const calculateRemaining = () => {
      const session = activeSession.session;
      const planned = session.planned_duration_seconds;
      const accumulated = session.accumulated_pause_seconds;
      const started = new Date(session.started_at).getTime();

      let effectiveElapsed = 0;
      if (session.status === 'PAUSED' && session.paused_at) {
        effectiveElapsed = Math.floor((new Date(session.paused_at).getTime() - started) / 1000) - accumulated;
      } else {
        const now = Date.now();
        effectiveElapsed = Math.floor((now - started) / 1000) - accumulated;
      }

      const remaining = Math.max(0, planned - Math.max(0, effectiveElapsed));
      setDisplaySeconds(remaining);

      // Auto-trigger complete if active and reached 0
      if (remaining === 0 && session.status === 'ACTIVE') {
        onComplete();
      }
    };

    calculateRemaining();

    if (activeSession.session.status === 'ACTIVE') {
      const interval = setInterval(calculateRemaining, 1000);
      return () => clearInterval(interval);
    }
  }, [activeSession, targetType, defaultDurations, onComplete]);

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isSessionActive = !!activeSession;
  const currentStatus = activeSession?.session.status;
  const currentType = activeSession?.session.session_type ?? targetType;

  // Calculate circular progress percentage
  const totalPlanned = activeSession ? activeSession.session.planned_duration_seconds : defaultDurations[targetType];
  const progressPercent = Math.min(100, Math.max(0, ((totalPlanned - displaySeconds) / totalPlanned) * 100));

  const handleStartSession = async (type: FocusSessionType) => {
    setTargetType(type);
    const duration = defaultDurations[type];
    await onStart(type, duration, selectedTaskId);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 flex flex-col items-center">
      {/* Session Type Tabs */}
      <div className="flex space-x-2 bg-gray-100 dark:bg-gray-700/60 p-1.5 rounded-xl mb-8">
        <button
          disabled={isSessionActive}
          onClick={() => {
            setTargetType('FOCUS');
            setDisplaySeconds(defaultDurations.FOCUS);
          }}
          className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            currentType === 'FOCUS'
              ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          } ${isSessionActive ? 'cursor-not-allowed opacity-80' : ''}`}
        >
          Focus
        </button>
        <button
          disabled={isSessionActive}
          onClick={() => {
            setTargetType('SHORT_BREAK');
            setDisplaySeconds(defaultDurations.SHORT_BREAK);
          }}
          className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            currentType === 'SHORT_BREAK'
              ? 'bg-white dark:bg-gray-800 text-emerald-600 dark:text-emerald-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          } ${isSessionActive ? 'cursor-not-allowed opacity-80' : ''}`}
        >
          Short Break
        </button>
        <button
          disabled={isSessionActive}
          onClick={() => {
            setTargetType('LONG_BREAK');
            setDisplaySeconds(defaultDurations.LONG_BREAK);
          }}
          className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            currentType === 'LONG_BREAK'
              ? 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          } ${isSessionActive ? 'cursor-not-allowed opacity-80' : ''}`}
        >
          Long Break
        </button>
      </div>

      {/* Circular Timer Display */}
      <div className="relative w-64 h-64 flex items-center justify-center my-4">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Track */}
          <circle
            cx="50"
            cy="50"
            r="44"
            className="text-gray-100 dark:text-gray-700 stroke-current"
            strokeWidth="6"
            fill="transparent"
          />
          {/* Progress */}
          <circle
            cx="50"
            cy="50"
            r="44"
            className={`transition-all duration-500 stroke-current ${
              currentType === 'FOCUS'
                ? 'text-indigo-600 dark:text-indigo-500'
                : currentType === 'SHORT_BREAK'
                ? 'text-emerald-500 dark:text-emerald-400'
                : 'text-blue-500 dark:text-blue-400'
            }`}
            strokeWidth="6"
            strokeDasharray={2 * Math.PI * 44}
            strokeDashoffset={2 * Math.PI * 44 * (1 - progressPercent / 100)}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>

        <div className="absolute flex flex-col items-center">
          <span
            data-testid="timer-display"
            className="text-5xl font-extrabold tracking-tight text-gray-900 dark:text-white font-mono"
          >
            {formatTime(displaySeconds)}
          </span>
          <span className="text-xs uppercase font-bold tracking-wider mt-2 text-gray-400 dark:text-gray-400">
            {currentStatus ?? 'READY'}
          </span>
        </div>
      </div>

      {/* Task Selector (Only editable when not active) */}
      <div className="w-full max-w-sm my-6">
        <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">
          Associated Task (Optional)
        </label>
        {isSessionActive && activeSession.session.task_title ? (
          <div className="px-3 py-2 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-lg text-sm font-medium text-indigo-700 dark:text-indigo-300 truncate">
            {activeSession.session.task_title}
          </div>
        ) : (
          <select
            disabled={isSessionActive}
            value={selectedTaskId ?? ''}
            onChange={(e) => onSelectTask(e.target.value ? e.target.value : null)}
            className="w-full bg-gray-50 dark:bg-gray-700/50 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:outline-none disabled:opacity-75 disabled:cursor-not-allowed"
          >
            <option value="">No task linked</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                {task.title}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-4 mt-2">
        {!isSessionActive ? (
          <button
            onClick={() => handleStartSession(targetType)}
            disabled={isLoading}
            className="flex items-center space-x-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50"
          >
            <Play className="w-5 h-5 fill-current" />
            <span>Start Focus</span>
          </button>
        ) : (
          <>
            {currentStatus === 'ACTIVE' ? (
              <button
                onClick={onPause}
                disabled={isLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl shadow transition-all focus:outline-none focus:ring-2 focus:ring-amber-400 disabled:opacity-50"
              >
                <Pause className="w-5 h-5 fill-current" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={onResume}
                disabled={isLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow transition-all focus:outline-none focus:ring-2 focus:ring-emerald-400 disabled:opacity-50"
              >
                <Play className="w-5 h-5 fill-current" />
                <span>Resume</span>
              </button>
            )}

            <button
              onClick={onComplete}
              disabled={isLoading}
              title="Finish session early"
              className="flex items-center space-x-2 px-5 py-3 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-semibold rounded-xl transition-all focus:outline-none disabled:opacity-50"
            >
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>Complete</span>
            </button>

            <button
              onClick={onSkip}
              disabled={isLoading}
              title="Skip to next session in cycle"
              className="flex items-center space-x-2 px-4 py-3 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/40 dark:hover:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 font-semibold rounded-xl transition-all focus:outline-none disabled:opacity-50"
            >
              <SkipForward className="w-5 h-5 fill-current" />
              <span>Skip</span>
            </button>

            <button
              onClick={onAbandon}
              disabled={isLoading}
              title="Abandon session"
              className="flex items-center space-x-2 px-4 py-3 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/40 text-rose-600 dark:text-rose-400 font-semibold rounded-xl transition-all focus:outline-none disabled:opacity-50"
            >
              <Square className="w-5 h-5 fill-current" />
              <span>Abandon</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};
