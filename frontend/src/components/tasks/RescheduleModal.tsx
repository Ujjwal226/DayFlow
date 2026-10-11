import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import type { Task, TaskReschedule } from '../../types/api';
import { toInputTime, fromInputTime, todayISO } from '../../lib/utils';
import { AlertCircle, Loader2 } from 'lucide-react';

interface RescheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: Task | null;
  onReschedule: (id: number, payload: TaskReschedule) => Promise<void>;
}

export const RescheduleModal: React.FC<RescheduleModalProps> = ({
  isOpen,
  onClose,
  task,
  onReschedule,
}) => {
  const [scheduledDate, setScheduledDate] = useState(todayISO());
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (task) {
      setScheduledDate(task.scheduled_date || todayISO());
      setStartTime(toInputTime(task.start_time));
      setEndTime(toInputTime(task.end_time));
    }
    setError(null);
  }, [task, isOpen]);

  if (!task) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!scheduledDate) {
      setError('Please choose a scheduled date');
      return;
    }

    if (startTime && endTime && endTime <= startTime) {
      setError('End time must be after start time');
      return;
    }

    setIsSubmitting(true);
    try {
      await onReschedule(task.id, {
        scheduled_date: scheduledDate,
        start_time: fromInputTime(startTime),
        end_time: fromInputTime(endTime),
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to reschedule task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reschedule Task"
      description={`Change the scheduled date and time for "${task.title}".`}
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="flex items-center space-x-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-xs text-[var(--text-secondary)] space-y-1">
          <p>
            <span className="font-semibold text-[var(--text-primary)]">Originally scheduled:</span>{' '}
            {task.original_scheduled_date || task.scheduled_date}
          </p>
          <p>
            <span className="font-semibold text-[var(--text-primary)]">Current scheduled date:</span>{' '}
            {task.scheduled_date}
          </p>
        </div>

        <div>
          <label htmlFor="reschedule-date" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
            New Scheduled Date <span className="text-rose-500">*</span>
          </label>
          <div className="relative">
            <input
              id="reschedule-date"
              type="date"
              required
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="reschedule-start-time" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              Start Time
            </label>
            <input
              id="reschedule-start-time"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>

          <div>
            <label htmlFor="reschedule-end-time" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              End Time
            </label>
            <input
              id="reschedule-end-time"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[var(--bg-border)]">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-xl text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center justify-center px-5 py-2 rounded-xl text-sm font-medium text-white bg-violet-600 hover:bg-violet-700 active:bg-violet-800 shadow-md shadow-violet-600/20 transition-all focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Rescheduling...
              </>
            ) : (
              'Reschedule Task'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
