import React from 'react';
import { KanbanFiltersState } from '../../types/kanban';
import { Project } from '../../types/project';
import { Category } from '../../types/category';
import { TaskPriority } from '../../types/task';
import {
  Search,
  Folder,
  Tag as TagIcon,
  AlertTriangle,
  Repeat,
  X,
  Plus,
  RefreshCw,
} from 'lucide-react';

interface KanbanToolbarProps {
  filters: KanbanFiltersState;
  onFilterChange: <K extends keyof KanbanFiltersState>(key: K, value: KanbanFiltersState[K]) => void;
  onResetFilters: () => void;
  projects: Project[];
  categories: Category[];
  totalTasks: number;
  filteredTasksCount: number;
  onNewTask: () => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const KanbanToolbar: React.FC<KanbanToolbarProps> = ({
  filters,
  onFilterChange,
  onResetFilters,
  projects,
  categories,
  totalTasks,
  filteredTasksCount,
  onNewTask,
  onRefresh,
  isLoading,
}) => {
  const isFiltered =
    filters.search.trim() !== '' ||
    filters.projectId !== 'ALL' ||
    filters.categoryId !== 'ALL' ||
    filters.priority !== 'ALL' ||
    filters.recurringOnly;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-xl backdrop-blur-md mb-6 space-y-3">
      {/* Top Row: Search, Actions */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search tasks by title or description..."
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition"
          />
          {filters.search && (
            <button
              onClick={() => onFilterChange('search', '')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Buttons & Status Counter */}
        <div className="flex items-center gap-2 flex-wrap justify-between md:justify-end">
          <div className="text-xs text-slate-400 font-medium px-2">
            Showing <span className="text-slate-200 font-semibold">{filteredTasksCount}</span> of{' '}
            <span className="text-slate-200">{totalTasks}</span> tasks
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 rounded-xl transition flex items-center gap-1.5 text-xs disabled:opacity-50"
            title="Refresh board"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={onNewTask}
            className="px-3.5 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>New Task</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Filter Dropdowns */}
      <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-800/70 text-xs">
        {/* Project Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950/40 border border-slate-800 rounded-lg px-2.5 py-1.5">
          <Folder className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filters.projectId}
            onChange={(e) => onFilterChange('projectId', e.target.value)}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            aria-label="Filter by project"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">
              All Projects
            </option>
            <option value="NO_PROJECT" className="bg-slate-900 text-slate-200">
              No Project
            </option>
            {projects.map((p) => (
              <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Category Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950/40 border border-slate-800 rounded-lg px-2.5 py-1.5">
          <TagIcon className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filters.categoryId}
            onChange={(e) => onFilterChange('categoryId', e.target.value)}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            aria-label="Filter by category"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">
              All Categories
            </option>
            {categories.map((c) => (
              <option key={c.id} value={c.id} className="bg-slate-900 text-slate-200">
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Priority Selector */}
        <div className="flex items-center gap-1.5 bg-slate-950/40 border border-slate-800 rounded-lg px-2.5 py-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filters.priority}
            onChange={(e) => onFilterChange('priority', e.target.value as TaskPriority | 'ALL')}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            aria-label="Filter by priority"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">
              All Priorities
            </option>
            <option value="LOW" className="bg-slate-900 text-slate-200">
              Low
            </option>
            <option value="MEDIUM" className="bg-slate-900 text-slate-200">
              Medium
            </option>
            <option value="HIGH" className="bg-slate-900 text-slate-200">
              High
            </option>
            <option value="URGENT" className="bg-slate-900 text-slate-200">
              Urgent
            </option>
          </select>
        </div>

        {/* Recurring Filter Toggle */}
        <button
          onClick={() => onFilterChange('recurringOnly', !filters.recurringOnly)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition ${
            filters.recurringOnly
              ? 'bg-purple-500/10 border-purple-500/30 text-purple-400 font-semibold'
              : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
          aria-pressed={filters.recurringOnly}
        >
          <Repeat className="w-3.5 h-3.5" />
          <span>Recurring Only</span>
        </button>

        {/* Reset Filters button */}
        {isFiltered && (
          <button
            onClick={onResetFilters}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 text-xs font-medium transition ml-auto"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear Filters</span>
          </button>
        )}
      </div>
    </div>
  );
};

