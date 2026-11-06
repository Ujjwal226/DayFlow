import React, { useState, useEffect } from 'react';
import { ScheduleTaskPayload } from '../../types/calendar';
import { tasksApi } from '../../api/tasks';
import { Task } from '../../types/task';
import { X, Clock, CheckCircle2, Search, AlertCircle, Layers } from 'lucide-react';

interface TaskSchedulingModalProps {
  isOpen: boolean;
  prefillDate?: Date | null;
  onClose: () => void;
  onSchedule: (payload: ScheduleTaskPayload) => Promise<void>;
}

export const TaskSchedulingModal: React.FC<TaskSchedulingModalProps> = ({
  isOpen,
  prefillDate,
  onClose,
  onSchedule,
}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const [startDateStr, setStartDateStr] = useState('');
  const [startTimeStr, setStartTimeStr] = useState('');
  const [endTimeStr, setEndTimeStr] = useState('');
  const [location, setLocation] = useState('');

  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    setError(null);
    setSelectedTask(null);
    setSearchQuery('');
    setLocation('');

    const base = prefillDate || new Date();
    const sDate = base.toISOString().slice(0, 10);
    setStartDateStr(sDate);

    const nowH = base.getHours();
    setStartTimeStr(`${String(nowH).padStart(2, '0')}:00`);
    setEndTimeStr(`${String(nowH + 1).padStart(2, '0')}:00`);

    // Fetch incomplete tasks to schedule
    const loadTasks = async () => {
      setIsLoadingTasks(true);
      try {
        const res = await tasksApi.listTasks({ is_archived: false, page_size: 50 });
        setTasks(res.items.filter((t: Task) => t.status !== 'COMPLETED' && t.status !== 'CANCELLED'));
      } catch {
        setError('Failed to load eligible tasks.');
      } finally {
        setIsLoadingTasks(false);
      }
    };

    loadTasks();
  }, [isOpen, prefillDate]);

  if (!isOpen) return null;

  const filteredTasks = tasks.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedTask) {
      setError('Please select a task to schedule.');
      return;
    }

    if (!startDateStr || !startTimeStr || !endTimeStr) {
      setError('Start date, start time, and end time are required.');
      return;
    }

    const startDt = new Date(`${startDateStr}T${startTimeStr}:00`);
    const endDt = new Date(`${startDateStr}T${endTimeStr}:00`);

    if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
      setError('Invalid date or time values.');
      return;
    }

    if (endDt <= startDt) {
      setError('End time must be strictly after start time.');
      return;
    }

    setIsSubmitting(true);
    try {
      const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      await onSchedule({
        task_id: selectedTask.id,
        start_at: startDt.toISOString(),
        end_at: endDt.toISOString(),
        timezone: userTz,
        location: location.trim() || null,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to schedule task time block.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="task-scheduling-title"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 id="task-scheduling-title" className="text-base font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Schedule Task Time Block</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleScheduleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Task Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Select Task <span className="text-rose-400">*</span>
            </label>
            <div className="relative mb-2">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks..."
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-xs focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="max-h-36 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950/40 p-1 space-y-1">
              {isLoadingTasks ? (
                <div className="p-3 text-center text-xs text-slate-500">Loading tasks...</div>
              ) : filteredTasks.length === 0 ? (
                <div className="p-3 text-center text-xs text-slate-500">No matching tasks found.</div>
              ) : (
                filteredTasks.map((t) => {
                  const isChosen = selectedTask?.id === t.id;
                  return (
                    <div
                      key={t.id}
                      onClick={() => setSelectedTask(t)}
                      className={`p-2 rounded-lg cursor-pointer text-xs flex items-center justify-between transition ${
                        isChosen
                          ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300'
                          : 'hover:bg-slate-800/60 text-slate-300 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <CheckCircle2
                          className={`w-3.5 h-3.5 flex-shrink-0 ${isChosen ? 'text-emerald-400' : 'text-slate-500'}`}
                        />
                        <span className="truncate font-medium">{t.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-400 font-mono">
                          {t.priority}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Selected Task Details Banner */}
          {selectedTask && (
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <Layers className="w-3.5 h-3.5" />
                <span>Selected: {selectedTask.title}</span>
              </div>
              {selectedTask.due_date && (
                <p className="text-slate-400">
                  Due: {new Date(selectedTask.due_date).toLocaleDateString()}
                </p>
              )}
            </div>
          )}

          {/* Scheduling Times */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Date</label>
              <input
                type="date"
                value={startDateStr}
                onChange={(e) => setStartDateStr(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Start Time</label>
              <input
                type="time"
                value={startTimeStr}
                onChange={(e) => setStartTimeStr(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">End Time</label>
              <input
                type="time"
                value={endTimeStr}
                onChange={(e) => setEndTimeStr(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>
          </div>

          {/* Optional Location */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Location or Link (optional)</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Focus desk or Meet link"
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs placeholder-slate-500"
            />
          </div>

          {/* Action buttons */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !selectedTask}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
            >
              {isSubmitting ? 'Scheduling...' : 'Schedule Time Block'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

