import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import type { Task, TaskCreate, TaskUpdate, Priority, Category } from '../../types/api';
import { todayISO, toInputTime, fromInputTime } from '../../lib/utils';
import { AlertCircle, Loader2 } from 'lucide-react';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskToEdit?: Task | null;
  onSubmit: (data: TaskCreate | TaskUpdate) => Promise<void>;
}

export const TaskModal: React.FC<TaskModalProps> = ({
  isOpen,
  onClose,
  taskToEdit,
  onSubmit,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [scheduledDate, setScheduledDate] = useState(todayISO());
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [priority, setPriority] = useState<Priority>('medium');
  const [category, setCategory] = useState<Category>('work');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (taskToEdit) {
      setTitle(taskToEdit.title);
      setDescription(taskToEdit.description || '');
      setScheduledDate(taskToEdit.scheduled_date);
      setStartTime(toInputTime(taskToEdit.start_time));
      setEndTime(toInputTime(taskToEdit.end_time));
      setPriority(taskToEdit.priority);
      setCategory(taskToEdit.category);
    } else {
      setTitle('');
      setDescription('');
      setScheduledDate(todayISO());
      setStartTime('');
      setEndTime('');
      setPriority('medium');
      setCategory('work');
    }
    setError(null);
  }, [taskToEdit, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError('Task title is required');
      return;
    }

    if (!scheduledDate) {
      setError('Scheduled date is required');
      return;
    }

    if (startTime && endTime) {
      if (endTime <= startTime) {
        setError('End time must be after start time');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      const payload: TaskCreate = {
        title: trimmedTitle,
        description: description.trim() ? description.trim() : null,
        scheduled_date: scheduledDate,
        start_time: fromInputTime(startTime),
        end_time: fromInputTime(endTime),
        priority,
        category,
      };

      await onSubmit(payload);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={taskToEdit ? 'Edit Task' : 'Create New Task'}
      description={
        taskToEdit
          ? 'Update the details of your scheduled task.'
          : 'Add a new action item to your DayFlow schedule.'
      }
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="flex items-center space-x-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Title */}
        <div>
          <label htmlFor="task-title" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
            Task Title <span className="text-rose-500">*</span>
          </label>
          <input
            id="task-title"
            type="text"
            required
            maxLength={255}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Design review with engineering"
            className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]/50 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-sm transition-all"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="task-description" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
            Description <span className="text-[var(--text-secondary)] font-normal normal-case">(optional)</span>
          </label>
          <textarea
            id="task-description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add relevant notes, checklist links, or context..."
            className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]/50 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-sm transition-all resize-none"
          />
        </div>

        {/* Date and Times Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label htmlFor="task-date" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              Scheduled Date <span className="text-rose-500">*</span>
            </label>
            <input
              id="task-date"
              type="date"
              required
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>

          <div>
            <label htmlFor="task-start-time" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              Start Time
            </label>
            <input
              id="task-start-time"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>

          <div>
            <label htmlFor="task-end-time" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              End Time
            </label>
            <input
              id="task-end-time"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
            />
          </div>
        </div>

        {/* Priority & Category Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="task-priority" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              Priority
            </label>
            <select
              id="task-priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all capitalize"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div>
            <label htmlFor="task-category" className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
              Category
            </label>
            <select
              id="task-category"
              value={category}
              onChange={(e) => setCategory(e.target.value as Category)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all capitalize"
            >
              <option value="work">Work</option>
              <option value="personal">Personal</option>
              <option value="learning">Learning</option>
              <option value="health">Health</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        {/* Form Actions */}
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
                Saving...
              </>
            ) : taskToEdit ? (
              'Save Changes'
            ) : (
              'Create Task'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
