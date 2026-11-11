import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  Check,
  ChevronLeft,
  ChevronRight,
  Target,
  ListTodo,
} from 'lucide-react';
import {
  PlanningPeriodType,
  PlanningObjective,
  PlanningObjectiveCreatePayload,
  PlanningPeriodSummary,
  Goal,
} from '../../types/goal';
import { goalsApi } from '../../api/goals';

interface PlanningBoardProps {
  goals: Goal[];
  initialPeriod?: PlanningPeriodType;
  onGoalUpdated?: () => void;
}

export const PlanningBoard: React.FC<PlanningBoardProps> = ({
  goals,
  initialPeriod = 'DAILY',
  onGoalUpdated,
}) => {
  const [periodType, setPeriodType] = useState<PlanningPeriodType>(initialPeriod);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [summary, setSummary] = useState<PlanningPeriodSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Objective Form
  const [newTitle, setNewTitle] = useState('');
  const [selectedGoalId, setSelectedGoalId] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const formatDateKey = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const loadObjectives = React.useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const dateStr = formatDateKey(currentDate);
      const res = await goalsApi.getPlanningSummary(periodType, dateStr);
      setSummary(res);
    } catch (err: unknown) {
      console.error('Failed to load planning objectives:', err);
      setError('Failed to load planning objectives');
    } finally {
      setIsLoading(false);
    }
  }, [periodType, currentDate]);

  React.useEffect(() => {
    loadObjectives();
  }, [loadObjectives]);

  const handlePrevDate = () => {
    const next = new Date(currentDate);
    if (periodType === 'DAILY') {
      next.setDate(next.getDate() - 1);
    } else if (periodType === 'WEEKLY') {
      next.setDate(next.getDate() - 7);
    } else {
      next.setMonth(next.getMonth() - 1);
    }
    setCurrentDate(next);
  };

  const handleNextDate = () => {
    const next = new Date(currentDate);
    if (periodType === 'DAILY') {
      next.setDate(next.getDate() + 1);
    } else if (periodType === 'WEEKLY') {
      next.setDate(next.getDate() + 7);
    } else {
      next.setMonth(next.getMonth() + 1);
    }
    setCurrentDate(next);
  };

  const handleCreateObjective = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const payload: PlanningObjectiveCreatePayload = {
        title: newTitle.trim(),
        period_type: periodType,
        period_date: formatDateKey(currentDate),
        goal_id: selectedGoalId || null,
      };
      await goalsApi.createPlanningObjective(payload);
      setNewTitle('');
      setSelectedGoalId('');
      setIsAdding(false);
      await loadObjectives();
      if (onGoalUpdated) onGoalUpdated();
    } catch (err: unknown) {
      console.error('Failed to create objective:', err);
      setError(err instanceof Error ? err.message : 'Failed to create objective');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleComplete = async (obj: PlanningObjective) => {
    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.updatePlanningObjective(obj.id, {
        is_completed: !obj.is_completed,
      });
      await loadObjectives();
      if (onGoalUpdated) onGoalUpdated();
    } catch (err: unknown) {
      console.error('Failed to toggle objective:', err);
      setError(err instanceof Error ? err.message : 'Failed to toggle objective');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteObjective = async (objectiveId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await goalsApi.deletePlanningObjective(objectiveId);
      await loadObjectives();
      if (onGoalUpdated) onGoalUpdated();
    } catch (err: unknown) {
      console.error('Failed to delete objective:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete objective');
    } finally {
      setIsLoading(false);
    }
  };

  const periodLabel = React.useMemo(() => {
    if (periodType === 'DAILY') {
      return currentDate.toLocaleDateString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } else if (periodType === 'WEEKLY') {
      const start = new Date(currentDate);
      start.setDate(start.getDate() - start.getDay() + 1);
      const end = new Date(start);
      end.setDate(end.getDate() + 6);
      return `Week of ${start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`;
    } else {
      return currentDate.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
      });
    }
  }, [periodType, currentDate]);

  const objectives = summary?.objectives || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      {/* Top Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ListTodo className="w-5 h-5 text-indigo-400" />
            Planning Alignment
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Break strategic milestones down into daily, weekly, and monthly commitments.
          </p>
        </div>

        {/* Period Selector Tabs */}
        <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          {(['DAILY', 'WEEKLY', 'MONTHLY'] as PlanningPeriodType[]).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setPeriodType(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                periodType === type
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {type.charAt(0) + type.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Date Navigation & Summary Metrics */}
      <div className="flex items-center justify-between py-4 border-b border-slate-800/60 text-xs">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handlePrevDate}
            className="p-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-semibold text-white px-2 min-w-[140px] text-center">
            {periodLabel}
          </span>
          <button
            type="button"
            onClick={handleNextDate}
            className="p-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {summary && (
          <div className="flex items-center gap-4 text-slate-400">
            <span>
              {summary.completed_objectives}/{summary.total_objectives} Completed
            </span>
            <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-indigo-500 h-full rounded-full transition-all"
                style={{
                  width: `${
                    summary.total_objectives > 0
                      ? Math.round((summary.completed_objectives / summary.total_objectives) * 100)
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="my-3 p-3 bg-rose-950/50 border border-rose-800/80 rounded-lg text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Objectives List */}
      <div className="mt-4 space-y-2">
        {objectives.length === 0 && !isAdding ? (
          <div className="py-8 text-center">
            <Target className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
            <p className="text-xs text-slate-400">
              No objectives scheduled for this {periodType.toLowerCase()} period.
            </p>
            <button
              type="button"
              onClick={() => setIsAdding(true)}
              className="mt-3 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Commitment
            </button>
          </div>
        ) : (
          objectives.map((obj) => (
            <div
              key={obj.id}
              className="flex items-center justify-between p-3 bg-slate-800/40 hover:bg-slate-800/60 border border-slate-800 rounded-xl transition group"
            >
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleToggleComplete(obj)}
                  className={`w-5 h-5 rounded-md border flex items-center justify-center transition ${
                    obj.is_completed
                      ? 'bg-emerald-600 border-emerald-500 text-white'
                      : 'bg-slate-800 border-slate-600 text-transparent hover:border-indigo-400'
                  }`}
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
                <div>
                  <span
                    className={`text-xs font-medium block ${
                      obj.is_completed ? 'line-through text-slate-500' : 'text-slate-200'
                    }`}
                  >
                    {obj.title}
                  </span>
                  {obj.goal_title && (
                    <span className="text-[10px] text-indigo-400 flex items-center gap-1 mt-0.5">
                      <Target className="w-3 h-3" />
                      Goal: {obj.goal_title}
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleDeleteObjective(obj.id)}
                className="p-1 text-slate-500 hover:text-rose-400 text-xs opacity-0 group-hover:opacity-100 transition"
                title="Delete Objective"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}

        {/* Add Objective Inline Form */}
        {isAdding && (
          <form
            onSubmit={handleCreateObjective}
            className="p-3 bg-slate-800/80 border border-slate-700 rounded-xl space-y-3 mt-3"
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Commitment description..."
                className="sm:col-span-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
                autoFocus
                required
              />
              <select
                value={selectedGoalId}
                onChange={(e) => setSelectedGoalId(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white"
              >
                <option value="">No Linked Goal</option>
                {goals.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsAdding(false)}
                className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
              >
                Add Objective
              </button>
            </div>
          </form>
        )}

        {objectives.length > 0 && !isAdding && (
          <button
            type="button"
            onClick={() => setIsAdding(true)}
            className="w-full py-2 border border-dashed border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium rounded-xl flex items-center justify-center gap-1.5 transition mt-2"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Another Objective
          </button>
        )}
      </div>
    </div>
  );
};
