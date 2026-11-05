import React, { useState } from 'react';
import {
  RecurringTask,
  RecurringTaskCreatePayload,
  RecurringTaskUpdatePayload,
  RecurrenceFrequency,
} from '../../types/recurringTask';
import { TaskPriority } from '../../types/task';
import { Category } from '../../types/category';
import { Project } from '../../types/project';
import { RecurrenceRuleSelector } from './RecurrenceRuleSelector';
import { AlertCircle, Loader2, X } from 'lucide-react';

interface RecurringTaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: RecurringTaskCreatePayload | RecurringTaskUpdatePayload) => Promise<void>;
  initialSeries?: RecurringTask | null;
  categories?: Category[];
  projects?: Project[];
}

export const RecurringTaskFormModal: React.FC<RecurringTaskFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialSeries,
  categories = [],
  projects = [],
}) => {
  const isEditing = !!initialSeries;

  const [title, setTitle] = useState(initialSeries?.title || '');
  const [description, setDescription] = useState(initialSeries?.description || '');
  const [priority, setPriority] = useState<TaskPriority>(initialSeries?.priority || 'MEDIUM');
  const [categoryId, setCategoryId] = useState<string>(initialSeries?.category_id || '');
  const [projectId, setProjectId] = useState<string>(initialSeries?.project_id || '');

  const [frequency, setFrequency] = useState<RecurrenceFrequency>(
    initialSeries?.frequency || 'DAILY'
  );
  const [interval, setInterval] = useState<number>(initialSeries?.interval || 1);
  const [weekdays, setWeekdays] = useState<number[]>(initialSeries?.weekdays || [1]); // Default Tuesday or Mon
  const [dayOfMonth, setDayOfMonth] = useState<number | null>(initialSeries?.day_of_month ?? null);
  const [monthOfYear, setMonthOfYear] = useState<number | null>(
    initialSeries?.month_of_year ?? null
  );

  const [startDate, setStartDate] = useState(
    initialSeries?.start_date || new Date().toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(initialSeries?.end_date || '');
  const [maxOccurrences, setMaxOccurrences] = useState<string>(
    initialSeries?.max_occurrences ? String(initialSeries.max_occurrences) : ''
  );

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync state if initialSeries changes
  React.useEffect(() => {
    if (initialSeries) {
      setTitle(initialSeries.title);
      setDescription(initialSeries.description || '');
      setPriority(initialSeries.priority);
      setCategoryId(initialSeries.category_id || '');
      setProjectId(initialSeries.project_id || '');
      setFrequency(initialSeries.frequency);
      setInterval(initialSeries.interval);
      setWeekdays(initialSeries.weekdays || [0]);
      setDayOfMonth(initialSeries.day_of_month);
      setMonthOfYear(initialSeries.month_of_year);
      setStartDate(initialSeries.start_date);
      setEndDate(initialSeries.end_date || '');
      setMaxOccurrences(
        initialSeries.max_occurrences ? String(initialSeries.max_occurrences) : ''
      );
    } else {
      setTitle('');
      setDescription('');
      setPriority('MEDIUM');
      setCategoryId('');
      setProjectId('');
      setFrequency('DAILY');
      setInterval(1);
      setWeekdays([0]);
      setDayOfMonth(null);
      setMonthOfYear(null);
      setStartDate(new Date().toISOString().split('T')[0]);
      setEndDate('');
      setMaxOccurrences('');
    }
    setError(null);
  }, [initialSeries, isOpen]);

  if (!isOpen) return null;

  const handleFrequencyChange = (newFreq: RecurrenceFrequency) => {
    setFrequency(newFreq);
    // Reset irrelevant rule properties to prevent carrying over stale settings
    if (newFreq !== 'WEEKLY') {
      setWeekdays([0]);
    }
    if (newFreq !== 'MONTHLY' && newFreq !== 'YEARLY') {
      setDayOfMonth(null);
    }
    if (newFreq !== 'YEARLY') {
      setMonthOfYear(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanTitle = title.trim();
    if (!cleanTitle) {
      setError('Title cannot be empty.');
      return;
    }

    if (!startDate) {
      setError('Start date is required.');
      return;
    }

    if (endDate && endDate < startDate) {
      setError('End date cannot be earlier than start date.');
      return;
    }

    if (frequency === 'WEEKLY' && weekdays.length === 0) {
      setError('Select at least one weekday for weekly recurrence.');
      return;
    }

    const payload: RecurringTaskCreatePayload = {
      title: cleanTitle,
      description: description.trim() ? description.trim() : null,
      priority,
      category_id: categoryId || null,
      project_id: projectId || null,
      frequency,
      interval,
      start_date: startDate,
      end_date: endDate || null,
      max_occurrences: maxOccurrences ? parseInt(maxOccurrences, 10) : null,
      weekdays: frequency === 'WEEKLY' ? weekdays : null,
      day_of_month: frequency === 'MONTHLY' || frequency === 'YEARLY' ? dayOfMonth : null,
      month_of_year: frequency === 'YEARLY' ? monthOfYear : null,
    };

    setIsSubmitting(true);
    try {
      await onSubmit(payload);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save recurring task.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 sm:p-8 my-8 text-slate-100">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white transition"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-bold tracking-tight text-white mb-1">
          {isEditing ? 'Edit Recurring Task Series' : 'Create Recurring Task Series'}
        </h2>
        <p className="text-xs text-slate-400 mb-6">
          Configure an automated schedule for tasks that repeat regularly.
        </p>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Series Title <span className="text-emerald-400">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Weekly Status Report"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Description
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Template task details and instructions..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
            />
          </div>

          {/* Priority & Category & Project */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">No Category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Project
              </label>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">No Project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Recurrence Rule Selector */}
          <RecurrenceRuleSelector
            frequency={frequency}
            interval={interval}
            weekdays={weekdays}
            dayOfMonth={dayOfMonth}
            monthOfYear={monthOfYear}
            onFrequencyChange={handleFrequencyChange}
            onIntervalChange={setInterval}
            onWeekdaysChange={setWeekdays}
            onDayOfMonthChange={setDayOfMonth}
            onMonthOfYearChange={setMonthOfYear}
            disabled={isSubmitting}
          />

          {/* Schedule Window: Start date, End date, Max occurrences */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Start Date <span className="text-emerald-400">*</span>
              </label>
              <input
                type="date"
                required
                value={startDate}
                disabled={isEditing} // Start date is immutable or base reference
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                End Date (Optional)
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Max Occurrences
              </label>
              <input
                type="number"
                min={1}
                max={1000}
                placeholder="Unlimited"
                value={maxOccurrences}
                onChange={(e) => setMaxOccurrences(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2.5 rounded-xl border border-slate-800 hover:bg-slate-800/60 text-slate-400 hover:text-white text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-2 disabled:opacity-50"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>{isEditing ? 'Save Changes' : 'Create Series'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

