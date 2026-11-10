import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PomodoroTimer } from '../components/focus/PomodoroTimer';
import { FocusPreference } from '../types/focus';
import { Task } from '../types/task';

describe('PomodoroTimer Component', () => {
  const mockPreferences: FocusPreference = {
    id: 'pref-1',
    user_id: 'user-1',
    focus_duration_minutes: 25,
    short_break_duration_minutes: 5,
    long_break_duration_minutes: 15,
    long_break_interval: 4,
    auto_start_breaks: false,
    auto_start_focus: false,
    sound_enabled: true,
    browser_notifications_enabled: true,
    daily_goal_minutes: 120,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockTasks: Task[] = [
    {
      id: 'task-1',
      user_id: 'user-1',
      title: 'Finish stage 3F report',
      status: 'IN_PROGRESS' as const,
      priority: 'HIGH' as const,
      description: null,
      due_date: null,
      start_date: null,
      parent_task_id: null,
      category_id: null,
      is_archived: false,
      is_overdue: false,
      completed_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const defaultProps = {
    activeSession: null,
    preferences: mockPreferences,
    tasks: mockTasks,
    selectedTaskId: null,
    onSelectTask: vi.fn(),
    onStart: vi.fn(),
    onPause: vi.fn(),
    onResume: vi.fn(),
    onComplete: vi.fn(),
    onAbandon: vi.fn(),
    onSkip: vi.fn(),
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial timer with default focus duration of 25:00', () => {
    render(<PomodoroTimer {...defaultProps} />);
    expect(screen.getByTestId('timer-display')).toHaveTextContent('25:00');
    expect(screen.getByText('Start Focus')).toBeInTheDocument();
  });

  it('switches duration when selecting break tabs', () => {
    render(<PomodoroTimer {...defaultProps} />);
    const shortBreakTab = screen.getByRole('button', { name: /short break/i });
    fireEvent.click(shortBreakTab);
    expect(screen.getByTestId('timer-display')).toHaveTextContent('05:00');

    const longBreakTab = screen.getByRole('button', { name: /long break/i });
    fireEvent.click(longBreakTab);
    expect(screen.getByTestId('timer-display')).toHaveTextContent('15:00');
  });

  it('calls onStart with appropriate params when clicking Start Focus', async () => {
    const onStart = vi.fn().mockResolvedValue(undefined);
    render(<PomodoroTimer {...defaultProps} onStart={onStart} />);
    const startBtn = screen.getByRole('button', { name: /start focus/i });
    fireEvent.click(startBtn);

    expect(onStart).toHaveBeenCalledWith('FOCUS', 25 * 60, null);
  });

  it('renders Pause, Complete, and Abandon buttons when a session is ACTIVE', () => {
    const activeSession = {
      session: {
        id: 'session-123',
        user_id: 'user-1',
        task_id: 'task-1',
        project_id: null,
        session_type: 'FOCUS' as const,
        status: 'ACTIVE' as const,
        planned_duration_seconds: 1500,
        actual_duration_seconds: 0,
        accumulated_pause_seconds: 0,
        started_at: new Date().toISOString(),
        paused_at: null,
        completed_at: null,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        task_title: 'Finish stage 3F report',
      },
      server_time: new Date().toISOString(),
      elapsed_seconds: 0,
      remaining_seconds: 1500,
      is_expired: false,
    };

    render(<PomodoroTimer {...defaultProps} activeSession={activeSession} />);
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /abandon/i })).toBeInTheDocument();
    expect(screen.getByText('Finish stage 3F report')).toBeInTheDocument();
  });

  it('renders Resume button when session is PAUSED', () => {
    const pausedSession = {
      session: {
        id: 'session-123',
        user_id: 'user-1',
        task_id: null,
        project_id: null,
        session_type: 'FOCUS' as const,
        status: 'PAUSED' as const,
        planned_duration_seconds: 1500,
        actual_duration_seconds: 100,
        accumulated_pause_seconds: 0,
        started_at: new Date(Date.now() - 100000).toISOString(),
        paused_at: new Date().toISOString(),
        completed_at: null,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      server_time: new Date().toISOString(),
      elapsed_seconds: 100,
      remaining_seconds: 1400,
      is_expired: false,
    };

    render(<PomodoroTimer {...defaultProps} activeSession={pausedSession} />);
    expect(screen.getByRole('button', { name: /resume/i })).toBeInTheDocument();
  });
});
