import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import type { Task, TaskEvent } from '../../types/api';
import { tasksApi } from '../../lib/api';
import { formatUTCDateTime } from '../../lib/utils';
import {
  Clock,
  Sparkles,
  Pencil,
  CheckCircle2,
  RotateCcw,
  Calendar,
  Trash2,
  Loader2,
  AlertCircle,
} from 'lucide-react';

interface TaskActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: Task | null;
}

export const TaskActivityModal: React.FC<TaskActivityModalProps> = ({
  isOpen,
  onClose,
  task,
}) => {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (task && isOpen) {
      setLoading(true);
      setError(null);
      tasksApi
        .getTaskHistory(task.id)
        .then((data) => setEvents(data))
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load activity'))
        .finally(() => setLoading(false));
    } else {
      setEvents([]);
    }
  }, [task, isOpen]);

  if (!task) return null;

  const getEventBadge = (eventType: string) => {
    switch (eventType) {
      case 'created':
        return {
          icon: Sparkles,
          label: 'Created',
          color: 'text-violet-400 bg-violet-400/10 border-violet-400/20',
        };
      case 'updated':
        return {
          icon: Pencil,
          label: 'Edited',
          color: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
        };
      case 'completed':
        return {
          icon: CheckCircle2,
          label: 'Completed',
          color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
        };
      case 'reopened':
        return {
          icon: RotateCcw,
          label: 'Reopened',
          color: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
        };
      case 'rescheduled':
        return {
          icon: Calendar,
          label: 'Rescheduled',
          color: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
        };
      case 'deleted':
        return {
          icon: Trash2,
          label: 'Soft Deleted',
          color: 'text-rose-400 bg-rose-400/10 border-rose-400/20',
        };
      default:
        return {
          icon: Clock,
          label: eventType,
          color: 'text-slate-400 bg-slate-400/10 border-slate-400/20',
        };
    }
  };

  const renderEventDetails = (event: TaskEvent) => {
    if (!event.details) return null;
    const d = event.details as Record<string, any>;

    if (event.event_type === 'rescheduled') {
      return (
        <div className="text-xs text-[var(--text-secondary)] mt-1.5 space-y-0.5 bg-[var(--bg-elevated)] p-2 rounded-lg border border-[var(--bg-border)]">
          <p>
            <span className="font-medium text-[var(--text-primary)]">From:</span>{' '}
            {d.previous_scheduled_date}{' '}
            {d.previous_start_time ? `(${d.previous_start_time.slice(0, 5)})` : ''}
          </p>
          <p>
            <span className="font-medium text-[var(--text-primary)]">To:</span>{' '}
            {d.new_scheduled_date}{' '}
            {d.new_start_time ? `(${d.new_start_time.slice(0, 5)})` : ''}
          </p>
        </div>
      );
    }

    if (event.event_type === 'updated' && d.changes) {
      const changes = d.changes as Record<string, { old: string | null; new: string | null }>;
      return (
        <div className="text-xs text-[var(--text-secondary)] mt-1.5 space-y-1 bg-[var(--bg-elevated)] p-2 rounded-lg border border-[var(--bg-border)]">
          {Object.entries(changes).map(([field, delta]) => (
            <p key={field}>
              <span className="font-medium capitalize text-[var(--text-primary)]">{field}:</span>{' '}
              <span className="line-through opacity-70">{delta.old || '(empty)'}</span> &rarr;{' '}
              <span className="text-violet-400 font-medium">{delta.new || '(empty)'}</span>
            </p>
          ))}
        </div>
      );
    }

    if (event.event_type === 'completed' && d.completed_at) {
      return (
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Marked finished at {formatUTCDateTime(d.completed_at)}
        </p>
      );
    }

    if (event.event_type === 'reopened') {
      return (
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Returned to pending status
        </p>
      );
    }

    return null;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Task Activity History"
      description={`Audit log and timeline for "${task.title}".`}
      maxWidth="lg"
    >
      <div className="space-y-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-8 space-y-2">
            <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
            <p className="text-xs text-[var(--text-secondary)]">Loading timeline...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : events.length === 0 ? (
          <div className="p-6 text-center text-xs text-[var(--text-secondary)] bg-[var(--bg-elevated)] rounded-xl border border-[var(--bg-border)]">
            No activity events recorded yet for this task.
          </div>
        ) : (
          <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[var(--bg-border)]">
            {events.map((evt) => {
              const badge = getEventBadge(evt.event_type);
              const Icon = badge.icon;
              return (
                <div key={evt.id} className="relative group">
                  <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[var(--bg-surface)] border-2 border-violet-500 flex items-center justify-center shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-xs font-semibold border ${badge.color}`}
                      >
                        <Icon className="w-3 h-3 mr-1" />
                        {badge.label}
                      </span>
                      <span className="text-xs text-[var(--text-secondary)]">
                        {formatUTCDateTime(evt.event_timestamp)}
                      </span>
                    </div>
                    {renderEventDetails(evt)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-[var(--bg-border)]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-[var(--text-primary)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-border)] transition-colors focus:outline-none"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
};
