import React, { useState } from 'react';
import { Task, TaskCreatePayload, TaskPriority, TaskStatus } from '../../types/task';
import { Category } from '../../types/category';
import { Tag } from '../../types/tag';
import { TagSelector } from '../tags/TagSelector';
import { AlertCircle, Check, Loader2, X } from 'lucide-react';

interface TaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: TaskCreatePayload) => Promise<void>;
  initialTask?: Task | null;
  categories?: Category[];
  tags?: Tag[];
}

export const TaskFormModal: React.FC<TaskFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialTask,
  categories = [],
  tags = [],
}) => {
  const [title, setTitle] = useState(initialTask?.title || '');
  const [description, setDescription] = useState(initialTask?.description || '');
  const [priority, setPriority] = useState<TaskPriority>(initialTask?.priority || 'MEDIUM');
  const [status, setStatus] = useState<TaskStatus>(initialTask?.status || 'TODO');
  const [categoryId, setCategoryId] = useState<string>(initialTask?.category_id || '');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(
    initialTask?.tags ? initialTask.tags.map((t) => t.id) : []
  );
  const [startDate, setStartDate] = useState(
    initialTask?.start_date ? initialTask.start_date.substring(0, 16) : ''
  );
  const [dueDate, setDueDate] = useState(
    initialTask?.due_date ? initialTask.due_date.substring(0, 16) : ''
  );

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync state if initialTask changes
  React.useEffect(() => {
    if (initialTask) {
      setTitle(initialTask.title);
      setDescription(initialTask.description || '');
      setPriority(initialTask.priority);
      setStatus(initialTask.status);
      setCategoryId(initialTask.category_id || '');
      setSelectedTagIds(initialTask.tags ? initialTask.tags.map((t) => t.id) : []);
      setStartDate(initialTask.start_date ? initialTask.start_date.substring(0, 16) : '');
      setDueDate(initialTask.due_date ? initialTask.due_date.substring(0, 16) : '');
    } else {
      setTitle('');
      setDescription('');
      setPriority('MEDIUM');
      setStatus('TODO');
      setCategoryId('');
      setSelectedTagIds([]);
      setStartDate('');
      setDueDate('');
    }
    setError(null);
  }, [initialTask, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError('Task title is required.');
      return;
    }
    if (trimmedTitle.length > 200) {
      setError('Title cannot exceed 200 characters.');
      return;
    }

    if (startDate && dueDate && new Date(dueDate) < new Date(startDate)) {
      setError('Due date cannot be earlier than start date.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        title: trimmedTitle,
        description: description.trim() ? description.trim() : null,
        priority,
        status,
        category_id: categoryId ? categoryId : null,
        tag_ids: selectedTagIds,
        start_date: startDate ? new Date(startDate).toISOString() : null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save task.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-6 sm:p-8 overflow-hidden text-slate-100 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <h2 className="text-xl font-bold text-white tracking-tight">
            {initialTask ? 'Edit Task' : 'Create New Task'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Task Title <span className="text-emerald-400">*</span>
            </label>
            <input
              type="text"
              required
              maxLength={200}
              placeholder="e.g., Finalize quarterly budget forecast"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white placeholder-slate-500 text-sm transition outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              placeholder="Add additional details, notes, or criteria..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white placeholder-slate-500 text-sm transition outline-none resize-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white text-sm transition outline-none"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white text-sm transition outline-none"
              >
                <option value="TODO">Todo</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          {/* Category Dropdown */}
          {categories.length > 0 && (
            <div>
              <label htmlFor="task-category-select" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Category (Optional)
              </label>
              <select
                id="task-category-select"
                aria-label="Category (Optional)"
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white text-sm transition outline-none"
              >
                <option value="">No Category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Tag Selector */}
          {tags.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Tags (Optional)
              </label>
              <TagSelector
                tags={tags}
                selectedTagIds={selectedTagIds}
                onChange={setSelectedTagIds}
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="task-start-date" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Start Date (Optional)
              </label>
              <input
                id="task-start-date"
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white text-sm transition outline-none"
              />
            </div>

            <div>
              <label htmlFor="task-due-date" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Due Date (Optional)
              </label>
              <input
                id="task-due-date"
                type="datetime-local"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white text-sm transition outline-none"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition shadow-lg shadow-emerald-500/20 flex items-center gap-1.5 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>{initialTask ? 'Update Task' : 'Create Task'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
