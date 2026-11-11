import React, { useState } from 'react';
import {
  X,
  Plus,
  Trash2,
  Calendar,
  CheckCircle2,
  ArrowUp,
  ArrowDown,
  Link as LinkIcon,
  Activity,
  Check,
} from 'lucide-react';
import { Goal, Milestone, MilestoneCreatePayload } from '../../types/goal';
import { Task } from '../../types/task';
import { goalsApi } from '../../api/goals';

interface GoalDetailModalProps {
  goal: Goal;
  isOpen: boolean;
  onClose: () => void;
  onGoalUpdated: (updatedGoal: Goal) => void;
  availableTasks?: Task[];
}

export const GoalDetailModal: React.FC<GoalDetailModalProps> = ({
  goal,
  isOpen,
  onClose,
  onGoalUpdated,
  availableTasks = [],
}) => {
  const [activeTab, setActiveTab] = useState<'milestones' | 'tasks' | 'activity'>('milestones');

  // Milestone creation form
  const [newMilestoneTitle, setNewMilestoneTitle] = useState('');
  const [newMilestoneDate, setNewMilestoneDate] = useState('');
  const [isAddingMilestone, setIsAddingMilestone] = useState(false);

  // Task linking
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [isLinkingTask, setIsLinkingTask] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMilestoneTitle.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const payload: MilestoneCreatePayload = {
        title: newMilestoneTitle.trim(),
        due_date: newMilestoneDate || null,
      };
      await goalsApi.createMilestone(goal.id, payload);
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
      setNewMilestoneTitle('');
      setNewMilestoneDate('');
      setIsAddingMilestone(false);
    } catch (err: unknown) {
      console.error('Failed to add milestone:', err);
      setError(err instanceof Error ? err.message : 'Failed to add milestone');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMilestone = async (milestone: Milestone) => {
    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.updateMilestone(milestone.id, {
        is_completed: !milestone.is_completed,
      });
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
    } catch (err: unknown) {
      console.error('Failed to toggle milestone:', err);
      setError(err instanceof Error ? err.message : 'Failed to toggle milestone');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteMilestone = async (milestoneId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.deleteMilestone(milestoneId);
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
    } catch (err: unknown) {
      console.error('Failed to delete milestone:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete milestone');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReorderMilestone = async (milestoneId: string, direction: 'up' | 'down') => {
    const sorted = [...(goal.milestones || [])].sort((a, b) => a.order_index - b.order_index);
    const index = sorted.findIndex((m) => m.id === milestoneId);
    if (index === -1) return;
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === sorted.length - 1) return;

    const swapIndex = direction === 'up' ? index - 1 : index + 1;
    const temp = sorted[index];
    sorted[index] = sorted[swapIndex];
    sorted[swapIndex] = temp;

    const items = sorted.map((m, idx) => ({ id: m.id, order_index: idx }));

    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.reorderMilestones(goal.id, items);
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
    } catch (err: unknown) {
      console.error('Failed to reorder milestones:', err);
      setError(err instanceof Error ? err.message : 'Failed to reorder milestones');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTaskId) return;

    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.linkTask(goal.id, selectedTaskId);
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
      setSelectedTaskId('');
      setIsLinkingTask(false);
    } catch (err: unknown) {
      console.error('Failed to link task:', err);
      setError(err instanceof Error ? err.message : 'Failed to link task');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnlinkTask = async (taskId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.unlinkTask(goal.id, taskId);
      const refreshed = await goalsApi.getGoal(goal.id);
      onGoalUpdated(refreshed);
    } catch (err: unknown) {
      console.error('Failed to unlink task:', err);
      setError(err instanceof Error ? err.message : 'Failed to unlink task');
    } finally {
      setIsLoading(false);
    }
  };

  const linkedTaskIds = new Set(goal.linked_tasks?.map((t) => t.id) || []);
  const unlinkedAvailableTasks = availableTasks.filter((t) => !linkedTaskIds.has(t.id));
  const sortedMilestones = [...(goal.milestones || [])].sort((a, b) => a.order_index - b.order_index);

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl relative my-8 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-300 capitalize">
                {goal.category.toLowerCase()}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                {goal.status.replace('_', ' ')}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white">{goal.title}</h2>
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
          <div className="mt-3 p-3 bg-rose-950/50 border border-rose-800/80 rounded-lg text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Goal Overview Bar */}
        <div className="my-4 p-4 bg-slate-800/40 rounded-xl border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Progress</span>
            <span className="text-base font-bold text-indigo-400">
              {Math.round(goal.progress_percentage || 0)}%
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Strategy</span>
            <span className="text-slate-200 font-medium capitalize">
              {goal.progress_method.toLowerCase()}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Priority</span>
            <span className="text-slate-200 font-medium capitalize">
              {goal.priority.toLowerCase()}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Target Date</span>
            <span className="text-slate-200 font-medium">
              {goal.target_date
                ? new Date(goal.target_date).toLocaleDateString()
                : 'None'}
            </span>
          </div>
        </div>

        {goal.description && (
          <p className="text-xs text-slate-300 leading-relaxed mb-4 bg-slate-800/20 p-3 rounded-lg border border-slate-800/60">
            {goal.description}
          </p>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 mb-4 gap-4 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab('milestones')}
            className={`pb-2.5 transition flex items-center gap-1.5 border-b-2 ${
              activeTab === 'milestones'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            Milestones ({goal.milestones?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('tasks')}
            className={`pb-2.5 transition flex items-center gap-1.5 border-b-2 ${
              activeTab === 'tasks'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <LinkIcon className="w-4 h-4" />
            Linked Tasks ({goal.linked_tasks?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('activity')}
            className={`pb-2.5 transition flex items-center gap-1.5 border-b-2 ${
              activeTab === 'activity'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            Activity
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="overflow-y-auto flex-1 pr-1 space-y-3">
          {/* MILESTONES TAB */}
          {activeTab === 'milestones' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  Track sequential checkpoints that contribute to goal completion.
                </span>
                {!isAddingMilestone && (
                  <button
                    type="button"
                    onClick={() => setIsAddingMilestone(true)}
                    className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 shadow-sm transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Milestone
                  </button>
                )}
              </div>

              {isAddingMilestone && (
                <form
                  onSubmit={handleAddMilestone}
                  className="p-3 bg-slate-800/80 border border-slate-700 rounded-xl space-y-3"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <input
                      type="text"
                      value={newMilestoneTitle}
                      onChange={(e) => setNewMilestoneTitle(e.target.value)}
                      placeholder="Milestone title..."
                      className="sm:col-span-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
                      autoFocus
                      required
                    />
                    <input
                      type="date"
                      value={newMilestoneDate}
                      onChange={(e) => setNewMilestoneDate(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIsAddingMilestone(false)}
                      className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
                    >
                      Save Milestone
                    </button>
                  </div>
                </form>
              )}

              {sortedMilestones.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">
                  No milestones added yet. Add one above to start tracking progress.
                </p>
              ) : (
                <div className="space-y-2">
                  {sortedMilestones.map((milestone, idx) => (
                    <div
                      key={milestone.id}
                      className="flex items-center justify-between p-3 bg-slate-800/40 hover:bg-slate-800/60 border border-slate-800 rounded-xl transition group"
                    >
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => handleToggleMilestone(milestone)}
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition ${
                            milestone.is_completed
                              ? 'bg-emerald-600 border-emerald-500 text-white'
                              : 'bg-slate-800 border-slate-600 text-transparent hover:border-indigo-400'
                          }`}
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <div>
                          <span
                            className={`text-xs font-medium block ${
                              milestone.is_completed
                                ? 'line-through text-slate-500'
                                : 'text-slate-200'
                            }`}
                          >
                            {milestone.title}
                          </span>
                          {milestone.due_date && (
                            <span className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                              <Calendar className="w-3 h-3" />
                              {new Date(milestone.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 transition">
                        <button
                          type="button"
                          disabled={idx === 0}
                          onClick={() => handleReorderMilestone(milestone.id, 'up')}
                          className="p-1 text-slate-400 hover:text-white disabled:opacity-20 text-xs"
                          title="Move Up"
                        >
                          <ArrowUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          disabled={idx === sortedMilestones.length - 1}
                          onClick={() => handleReorderMilestone(milestone.id, 'down')}
                          className="p-1 text-slate-400 hover:text-white disabled:opacity-20 text-xs"
                          title="Move Down"
                        >
                          <ArrowDown className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteMilestone(milestone.id)}
                          className="p-1 text-slate-400 hover:text-rose-400 text-xs ml-1"
                          title="Delete Milestone"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TASKS TAB */}
          {activeTab === 'tasks' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  Connect daily execution tasks to this strategic goal.
                </span>
                {!isLinkingTask && unlinkedAvailableTasks.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setIsLinkingTask(true)}
                    className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 shadow-sm transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Link Task
                  </button>
                )}
              </div>

              {isLinkingTask && (
                <form
                  onSubmit={handleLinkTask}
                  className="p-3 bg-slate-800/80 border border-slate-700 rounded-xl space-y-3"
                >
                  <label className="block text-xs font-medium text-slate-300">
                    Select an existing task to link:
                  </label>
                  <select
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
                    required
                  >
                    <option value="">-- Choose Task --</option>
                    {unlinkedAvailableTasks.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title} ({t.status})
                      </option>
                    ))}
                  </select>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIsLinkingTask(false)}
                      className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading || !selectedTaskId}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
                    >
                      Link
                    </button>
                  </div>
                </form>
              )}

              {(!goal.linked_tasks || goal.linked_tasks.length === 0) ? (
                <p className="text-xs text-slate-500 py-6 text-center">
                  No tasks linked to this goal yet.
                </p>
              ) : (
                <div className="space-y-2">
                  {goal.linked_tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-3 bg-slate-800/40 border border-slate-800 rounded-xl"
                    >
                      <div>
                        <span className="text-xs font-medium text-slate-200 block">
                          {task.title}
                        </span>
                        <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                          <span>Status: {task.status}</span>
                          <span>Priority: {task.priority}</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleUnlinkTask(task.id)}
                        className="p-1 text-slate-400 hover:text-rose-400 text-xs"
                        title="Unlink Task"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ACTIVITY TAB */}
          {activeTab === 'activity' && (
            <div className="space-y-2 text-center py-6 text-xs text-slate-400">
              Audit activity logs are tracked securely in the database for each lifecycle mutation.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
