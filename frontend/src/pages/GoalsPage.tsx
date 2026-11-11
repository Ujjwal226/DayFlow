import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Target,
  Plus,
  Search,
  LayoutGrid,
  List,
  Calendar as CalendarIcon,
  RefreshCw,
} from 'lucide-react';
import {
  Goal,
  GoalStatus,
  GoalAnalyticsOverview,
  GoalCreatePayload,
  GoalUpdatePayload,
} from '../types/goal';
import { Task } from '../types/task';
import { Project } from '../types/project';
import { goalsApi } from '../api/goals';
import { tasksApi } from '../api/tasks';
import { projectsApi } from '../api/projects';

import { GoalCard } from '../components/goals/GoalCard';
import { GoalFormModal } from '../components/goals/GoalFormModal';
import { GoalDetailModal } from '../components/goals/GoalDetailModal';
import { GoalAnalyticsCard } from '../components/goals/GoalAnalyticsCard';
import { PlanningBoard } from '../components/goals/PlanningBoard';

type ViewMode = 'list' | 'board' | 'timeline';

const STATUS_COLUMNS: { status: GoalStatus; label: string; color: string }[] = [
  { status: 'NOT_STARTED', label: 'Not Started', color: 'border-slate-700 bg-slate-900/40' },
  { status: 'IN_PROGRESS', label: 'In Progress', color: 'border-indigo-900/40 bg-indigo-950/20' },
  { status: 'ON_TRACK', label: 'On Track', color: 'border-emerald-900/40 bg-emerald-950/20' },
  { status: 'AT_RISK', label: 'At Risk', color: 'border-rose-900/40 bg-rose-950/20' },
  { status: 'COMPLETED', label: 'Completed', color: 'border-teal-900/40 bg-teal-950/20' },
];

export const GoalsPage: React.FC = () => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [analytics, setAnalytics] = useState<GoalAnalyticsOverview | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // View & Filter states
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');

  // Modals
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [selectedGoalDetail, setSelectedGoalDetail] = useState<Goal | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [goalsRes, analyticsRes, tasksRes, projectsRes] = await Promise.all([
        goalsApi.listGoals({ page_size: 100 }),
        goalsApi.getAnalytics(),
        tasksApi.listTasks({ page_size: 100 }),
        projectsApi.list({ page_size: 100 }),
      ]);
      setGoals(goalsRes.items || []);
      setAnalytics(analyticsRes);
      setTasks(tasksRes.items || []);
      setProjects(projectsRes.items || []);
    } catch (err: unknown) {
      console.error('Failed to load goals data:', err);
      setError('Failed to load goals data. Please check connection.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Goal Form Submission
  const handleSaveGoal = async (data: GoalCreatePayload | GoalUpdatePayload) => {
    if (editingGoal) {
      await goalsApi.updateGoal(editingGoal.id, data as GoalUpdatePayload);
    } else {
      await goalsApi.createGoal(data as GoalCreatePayload);
    }
    await loadData();
    setIsFormOpen(false);
    setEditingGoal(null);
  };

  // Completion Toggle
  const handleToggleComplete = async (goal: Goal) => {
    try {
      if (goal.status === 'COMPLETED') {
        await goalsApi.reopenGoal(goal.id);
      } else {
        await goalsApi.completeGoal(goal.id);
      }
      await loadData();
      if (selectedGoalDetail && selectedGoalDetail.id === goal.id) {
        const refreshed = await goalsApi.getGoal(goal.id);
        setSelectedGoalDetail(refreshed);
      }
    } catch (err: unknown) {
      console.error('Failed to update status:', err);
      setError(err instanceof Error ? err.message : 'Failed to update goal');
    }
  };

  // Delete Goal
  const handleDeleteGoal = async (goalId: string) => {
    if (!window.confirm('Are you sure you want to delete this goal and its milestones?')) {
      return;
    }
    try {
      await goalsApi.deleteGoal(goalId);
      await loadData();
      if (selectedGoalDetail?.id === goalId) {
        setSelectedGoalDetail(null);
      }
    } catch (err: unknown) {
      console.error('Failed to delete goal:', err);
      setError('Failed to delete goal');
    }
  };

  // Filtered Goals
  const filteredGoals = useMemo(() => {
    return goals.filter((g) => {
      if (
        searchQuery &&
        !g.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !g.description?.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false;
      }
      if (selectedCategory !== 'ALL' && g.category !== selectedCategory) {
        return false;
      }
      if (selectedStatus !== 'ALL' && g.status !== selectedStatus) {
        return false;
      }
      if (selectedPriority !== 'ALL' && g.priority !== selectedPriority) {
        return false;
      }
      return true;
    });
  }, [goals, searchQuery, selectedCategory, selectedStatus, selectedPriority]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Target className="w-7 h-7 text-indigo-400" />
              Strategic Goals & Planning
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Connect high-level aspirations to daily execution with milestones and tracking.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => loadData()}
              disabled={isLoading}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
              title="Refresh Goals"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={() => {
                setEditingGoal(null);
                setIsFormOpen(true);
              }}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 flex items-center gap-1.5 transition"
            >
              <Plus className="w-4 h-4" />
              New Strategic Goal
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Analytics Card */}
        <GoalAnalyticsCard analytics={analytics} isLoading={isLoading} />

        {/* Planning Alignment Section */}
        <PlanningBoard goals={goals} onGoalUpdated={loadData} />

        {/* Controls, Search & Filter Bar */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto flex-1">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search goals..."
                className="w-full bg-slate-800/70 border border-slate-700/60 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-800/70 border border-slate-700/60 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Categories</option>
              <option value="PERSONAL">Personal</option>
              <option value="CAREER">Career</option>
              <option value="LEARNING">Learning</option>
              <option value="HEALTH">Health</option>
              <option value="FINANCE">Finance</option>
              <option value="PROJECTS">Projects</option>
              <option value="OTHER">Other</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-800/70 border border-slate-700/60 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="NOT_STARTED">Not Started</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ON_TRACK">On Track</option>
              <option value="AT_RISK">At Risk</option>
              <option value="COMPLETED">Completed</option>
            </select>

            {/* Priority Filter */}
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="bg-slate-800/70 border border-slate-700/60 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-800/70 p-1 rounded-xl border border-slate-700/60 self-end md:self-auto">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === 'list'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('board')}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === 'board'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Board View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('timeline')}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === 'timeline'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Timeline / Deadline View"
            >
              <CalendarIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* VIEW: LIST */}
        {viewMode === 'list' && (
          <div>
            {filteredGoals.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
                <Target className="w-12 h-12 text-slate-600 mx-auto mb-3 opacity-40" />
                <h3 className="text-base font-semibold text-white">No goals found</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  {goals.length === 0
                    ? 'Start by creating your first strategic goal to map out your long-term ambitions.'
                    : 'No goals match your active search or filter criteria.'}
                </p>
                {goals.length === 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingGoal(null);
                      setIsFormOpen(true);
                    }}
                    className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" />
                    Create First Goal
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredGoals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    onSelect={(g) => setSelectedGoalDetail(g)}
                    onEdit={(g) => {
                      setEditingGoal(g);
                      setIsFormOpen(true);
                    }}
                    onDelete={handleDeleteGoal}
                    onToggleComplete={handleToggleComplete}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* VIEW: BOARD (Kanban by Status) */}
        {viewMode === 'board' && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 overflow-x-auto pb-4">
            {STATUS_COLUMNS.map((col) => {
              const colGoals = filteredGoals.filter((g) => g.status === col.status);
              return (
                <div
                  key={col.status}
                  className={`border rounded-2xl p-4 flex flex-col min-h-[400px] ${col.color}`}
                >
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      {col.label}
                    </span>
                    <span className="text-xs font-bold bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700/60">
                      {colGoals.length}
                    </span>
                  </div>

                  <div className="space-y-3 flex-1 overflow-y-auto pr-0.5">
                    {colGoals.map((goal) => (
                      <GoalCard
                        key={goal.id}
                        goal={goal}
                        onSelect={(g) => setSelectedGoalDetail(g)}
                        onEdit={(g) => {
                          setEditingGoal(g);
                          setIsFormOpen(true);
                        }}
                        onDelete={handleDeleteGoal}
                        onToggleComplete={handleToggleComplete}
                      />
                    ))}
                    {colGoals.length === 0 && (
                      <div className="text-center py-10 text-[11px] text-slate-600">
                        No goals
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* VIEW: TIMELINE / DEADLINE */}
        {viewMode === 'timeline' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-indigo-400" />
              Target Deadlines Timeline
            </h3>

            {filteredGoals.filter((g) => g.target_date).length === 0 ? (
              <p className="text-xs text-slate-500 py-8 text-center">
                None of your filtered goals have target dates set.
              </p>
            ) : (
              <div className="relative border-l border-slate-800 ml-4 pl-6 space-y-6">
                {filteredGoals
                  .filter((g) => g.target_date)
                  .sort(
                    (a, b) =>
                      new Date(a.target_date!).getTime() - new Date(b.target_date!).getTime()
                  )
                  .map((goal) => {
                    const d = new Date(goal.target_date!);
                    const isOverdue =
                      goal.status !== 'COMPLETED' &&
                      d.setHours(23, 59, 59, 999) < Date.now();
                    return (
                      <div key={goal.id} className="relative group">
                        {/* Timeline Bullet */}
                        <div
                          className={`absolute -left-[31px] top-1.5 w-3 h-3 rounded-full border-2 border-slate-950 ${
                            goal.status === 'COMPLETED'
                              ? 'bg-teal-500'
                              : isOverdue
                              ? 'bg-rose-500'
                              : 'bg-indigo-500'
                          }`}
                        />
                        <div className="bg-slate-800/40 border border-slate-800 hover:border-slate-700 rounded-xl p-4 transition">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-300">
                              {new Date(goal.target_date!).toLocaleDateString(undefined, {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })}
                            </span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                                goal.status === 'COMPLETED'
                                  ? 'bg-teal-950/60 text-teal-300 border-teal-800'
                                  : isOverdue
                                  ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                                  : 'bg-slate-800 text-slate-300 border-slate-700'
                              }`}
                            >
                              {goal.status.replace('_', ' ')}
                            </span>
                          </div>
                          <h4
                            onClick={() => setSelectedGoalDetail(goal)}
                            className="font-bold text-sm text-white hover:text-indigo-400 cursor-pointer mt-1"
                          >
                            {goal.title}
                          </h4>
                          <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                            <span>Progress: {Math.round(goal.progress_percentage || 0)}%</span>
                            <span>•</span>
                            <span>{goal.milestones?.length || 0} milestones</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Form Modal (Create / Edit) */}
      <GoalFormModal
        isOpen={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setEditingGoal(null);
        }}
        onSubmit={handleSaveGoal}
        initialGoal={editingGoal}
        projects={projects}
      />

      {/* Detail Modal */}
      {selectedGoalDetail && (
        <GoalDetailModal
          goal={selectedGoalDetail}
          isOpen={true}
          onClose={() => setSelectedGoalDetail(null)}
          onGoalUpdated={(updated) => {
            setSelectedGoalDetail(updated);
            loadData();
          }}
          availableTasks={tasks}
        />
      )}
    </div>
  );
};
