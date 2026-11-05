import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';

interface ActivityFiltersProps {
  actionFilter: string;
  setActionFilter: (val: string) => void;
  entityFilter: string;
  setEntityFilter: (val: string) => void;
  startDate: string;
  setStartDate: (val: string) => void;
  endDate: string;
  setEndDate: (val: string) => void;
  onReset: () => void;
}

export const ActivityFilters: React.FC<ActivityFiltersProps> = ({
  actionFilter,
  setActionFilter,
  entityFilter,
  setEntityFilter,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  onReset,
}) => {
  return (
    <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 mb-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300 font-medium text-sm">
          <Filter className="w-4 h-4 text-emerald-400" />
          <span>Filter Activities</span>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition"
          title="Reset all filters"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {/* Entity Type Filter */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Entity Type
          </label>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Entities</option>
            <option value="TASK">Task</option>
            <option value="SUBTASK">Subtask</option>
            <option value="PROJECT">Project</option>
            <option value="RECURRING_TASK">Recurring Task</option>
            <option value="CATEGORY">Category</option>
            <option value="TAG">Tag</option>
          </select>
        </div>

        {/* Action Filter */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Action
          </label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Actions</option>
            <option value="TASK_CREATED">Task Created</option>
            <option value="TASK_UPDATED">Task Updated</option>
            <option value="TASK_COMPLETED">Task Completed</option>
            <option value="TASK_REOPENED">Task Reopened</option>
            <option value="TASK_DELETED">Task Deleted</option>
            <option value="TASK_DUPLICATED">Task Duplicated</option>
            <option value="TASK_ARCHIVED">Task Archived</option>
            <option value="TASK_RESTORED">Task Restored</option>
            <option value="SUBTASK_CREATED">Subtask Created</option>
            <option value="SUBTASK_COMPLETED">Subtask Completed</option>
            <option value="SUBTASK_DELETED">Subtask Deleted</option>
            <option value="PROJECT_CREATED">Project Created</option>
            <option value="PROJECT_UPDATED">Project Updated</option>
            <option value="PROJECT_DELETED">Project Deleted</option>
            <option value="RECURRING_SERIES_CREATED">Series Created</option>
            <option value="RECURRING_OCCURRENCE_GENERATED">Occurrence Generated</option>
            <option value="CATEGORY_CREATED">Category Created</option>
            <option value="TAG_CREATED">Tag Created</option>
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            From Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            To Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>
    </div>
  );
};

