import React, { useState } from 'react';
import { X, Target, BarChart2 } from 'lucide-react';
import {
  Goal,
  GoalCategory,
  GoalType,
  GoalPriority,
  GoalStatus,
  ProgressCalculationMethod,
  GoalCreatePayload,
  GoalUpdatePayload,
} from '../../types/goal';
import { Project } from '../../types/project';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: GoalCreatePayload | GoalUpdatePayload) => Promise<void>;
  initialGoal?: Goal | null;
  projects?: Project[];
}

export const GoalFormModal: React.FC<GoalFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialGoal,
  projects = [],
}) => {
  const isEditing = !!initialGoal;

  const [title, setTitle] = useState(initialGoal?.title || '');
  const [description, setDescription] = useState(initialGoal?.description || '');
  const [category, setCategory] = useState<GoalCategory>(initialGoal?.category || 'PERSONAL');
  const [goalType, setGoalType] = useState<GoalType>(initialGoal?.goal_type || 'OUTCOME');
  const [priority, setPriority] = useState<GoalPriority>(initialGoal?.priority || 'MEDIUM');
  const [status] = useState<GoalStatus>(initialGoal?.status || 'NOT_STARTED');
  const [progressMethod, setProgressMethod] = useState<ProgressCalculationMethod>(
    initialGoal?.progress_method || 'MANUAL'
  );
  const [targetValue, setTargetValue] = useState<number | undefined>(
    initialGoal?.target_value !== null ? initialGoal?.target_value : undefined
  );
  const [currentValue, setCurrentValue] = useState<number | undefined>(
    initialGoal?.current_value !== null ? initialGoal?.current_value : 0
  );
  const [unit, setUnit] = useState(initialGoal?.unit || '');
  const [manualProgress, setManualProgress] = useState<number>(
    initialGoal?.progress_percentage ? Math.round(initialGoal.progress_percentage) : 0
  );
  const [startDate, setStartDate] = useState(
    initialGoal?.start_date ? initialGoal.start_date.split('T')[0] : ''
  );
  const [targetDate, setTargetDate] = useState(
    initialGoal?.target_date ? initialGoal.target_date.split('T')[0] : ''
  );
  const [projectId, setProjectId] = useState<string | undefined>(
    initialGoal?.project_id || undefined
  );

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    if (progressMethod === 'NUMERIC' && (!targetValue || targetValue <= 0)) {
      setError('Target value must be greater than 0 for numeric goals');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const payload: GoalCreatePayload = {
        title: title.trim(),
        description: description.trim() || null,
        category,
        goal_type: goalType,
        priority,
        status,
        progress_method: progressMethod,
        target_value: progressMethod === 'NUMERIC' ? targetValue : null,
        current_value: progressMethod === 'NUMERIC' ? (currentValue || 0) : null,
        unit: progressMethod === 'NUMERIC' ? unit.trim() || null : null,
        progress_percentage: progressMethod === 'MANUAL' ? manualProgress : 0,
        start_date: startDate || null,
        target_date: targetDate || null,
        project_id: projectId || null,
      };

      await onSubmit(payload);
      onClose();
    } catch (err: unknown) {
      console.error('Error saving goal:', err);
      setError(err instanceof Error ? err.message : 'Failed to save goal');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl relative my-8">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold text-white">
              {isEditing ? 'Edit Goal' : 'Create New Goal'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-950/50 border border-rose-800/80 rounded-lg text-rose-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Master Rust Concurrency Patterns"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Context, motivation, and definition of done..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          {/* Category, Goal Type, Priority */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as GoalCategory)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="PERSONAL">Personal</option>
                <option value="CAREER">Career</option>
                <option value="LEARNING">Learning</option>
                <option value="HEALTH">Health</option>
                <option value="FINANCE">Finance</option>
                <option value="PROJECTS">Projects</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Goal Type</label>
              <select
                value={goalType}
                onChange={(e) => setGoalType(e.target.value as GoalType)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="OUTCOME">Outcome</option>
                <option value="NUMERIC">Numeric Target</option>
                <option value="MILESTONE">Milestones</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as GoalPriority)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          {/* Progress Calculation Mode */}
          <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-medium text-indigo-300">
              <BarChart2 className="w-4 h-4" />
              <span>Progress Calculation Strategy</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {(['MANUAL', 'MILESTONE', 'NUMERIC'] as ProgressCalculationMethod[]).map((method) => (
                <button
                  key={method}
                  type="button"
                  onClick={() => setProgressMethod(method)}
                  className={`py-2 px-3 rounded-lg text-xs font-medium border text-center transition ${
                    progressMethod === method
                      ? 'bg-indigo-600 border-indigo-500 text-white'
                      : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {method === 'MANUAL' ? 'Manual %' : method === 'MILESTONE' ? 'Milestone-based' : 'Numeric Target'}
                </button>
              ))}
            </div>

            {progressMethod === 'MANUAL' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Manual Progress: {manualProgress}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={manualProgress}
                  onChange={(e) => setManualProgress(parseInt(e.target.value, 10))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            )}

            {progressMethod === 'NUMERIC' && (
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Target Value *</label>
                  <input
                    type="number"
                    step="any"
                    value={targetValue ?? ''}
                    onChange={(e) => setTargetValue(e.target.value ? parseFloat(e.target.value) : undefined)}
                    placeholder="100"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Current Value</label>
                  <input
                    type="number"
                    step="any"
                    value={currentValue ?? ''}
                    onChange={(e) => setCurrentValue(e.target.value ? parseFloat(e.target.value) : 0)}
                    placeholder="0"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Unit</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    placeholder="km, pages, $"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-xs"
                  />
                </div>
              </div>
            )}

            {progressMethod === 'MILESTONE' && (
              <p className="text-xs text-slate-400">
                Progress will automatically compute as completed milestones divided by total milestones.
              </p>
            )}
          </div>

          {/* Dates & Project */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Date</label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Associated Project</label>
              <select
                value={projectId || ''}
                onChange={(e) => setProjectId(e.target.value || undefined)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
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

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg border border-slate-700 text-slate-300 hover:text-white text-xs font-medium hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : isEditing ? 'Update Goal' : 'Create Goal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
