import React, { useState, useEffect } from 'react';
import { Project } from '../../types/project';
import { Category } from '../../types/category';
import { projectsApi } from '../../api/projects';
import { categoriesApi } from '../../api/categories';
import { Filter, X, Check } from 'lucide-react';

export interface CalendarFilterState {
  includeTasks: boolean;
  includeEvents: boolean;
  projectId: string | null;
  categoryId: string | null;
  status: 'TODO' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | null;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT' | null;
  recurringOnly: boolean;
}

interface CalendarFilterDrawerProps {
  isOpen: boolean;
  filters: CalendarFilterState;
  onClose: () => void;
  onApplyFilters: (filters: CalendarFilterState) => void;
  onResetFilters: () => void;
}

export const CalendarFilterDrawer: React.FC<CalendarFilterDrawerProps> = ({
  isOpen,
  filters,
  onClose,
  onApplyFilters,
  onResetFilters,
}) => {
  const [localFilters, setLocalFilters] = useState<CalendarFilterState>(filters);
  const [projects, setProjects] = useState<Project[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  useEffect(() => {
    if (!isOpen) return;
    const loadMetadata = async () => {
      try {
        const [projRes, catRes] = await Promise.all([
          projectsApi.list({ is_archived: false, page_size: 100 }),
          categoriesApi.listCategories(),
        ]);
        setProjects(projRes.items);
        setCategories(catRes);
      } catch {
        // Silently tolerate if filters dropdown fails to populate
      }
    };
    loadMetadata();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleApply = () => {
    onApplyFilters(localFilters);
    onClose();
  };

  const handleReset = () => {
    onResetFilters();
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex justify-end"
      role="dialog"
      aria-modal="true"
      aria-labelledby="filter-drawer-title"
    >
      <div className="w-full max-w-sm bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-emerald-400" />
            <h2 id="filter-drawer-title" className="text-sm font-bold text-white">
              Calendar Filters
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            aria-label="Close filters"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filter Controls */}
        <div className="p-5 space-y-5 overflow-y-auto flex-1 text-xs">
          {/* Include Toggles */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Item Types
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={localFilters.includeEvents}
                  onChange={(e) =>
                    setLocalFilters({ ...localFilters, includeEvents: e.target.checked })
                  }
                  className="rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
                />
                <span>Include Calendar Events</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={localFilters.includeTasks}
                  onChange={(e) =>
                    setLocalFilters({ ...localFilters, includeTasks: e.target.checked })
                  }
                  className="rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
                />
                <span>Include Task Deadlines</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={localFilters.recurringOnly}
                  onChange={(e) =>
                    setLocalFilters({ ...localFilters, recurringOnly: e.target.checked })
                  }
                  className="rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
                />
                <span>Recurring Occurrences Only</span>
              </label>
            </div>
          </div>

          {/* Project Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Project
            </label>
            <select
              value={localFilters.projectId || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, projectId: e.target.value || null })
              }
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Category
            </label>
            <select
              value={localFilters.categoryId || ''}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, categoryId: e.target.value || null })
              }
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Task Status */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Task Status
            </label>
            <select
              value={localFilters.status || ''}
              onChange={(e) =>
                setLocalFilters({
                  ...localFilters,
                  status: (e.target.value as CalendarFilterState['status']) || null,
                })
              }
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Statuses</option>
              <option value="TODO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Task Priority
            </label>
            <select
              value={localFilters.priority || ''}
              onChange={(e) =>
                setLocalFilters({
                  ...localFilters,
                  priority: (e.target.value as CalendarFilterState['priority']) || null,
                })
              }
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Priorities</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Reset
          </button>
          <button
            onClick={handleApply}
            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Apply Filters</span>
          </button>
        </div>
      </div>
    </div>
  );
};

