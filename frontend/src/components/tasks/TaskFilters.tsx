import React from 'react';
import { TaskFilterParams, TaskPriority, TaskStatus } from '../../types/task';
import { Category } from '../../types/category';
import { Tag } from '../../types/tag';
import { Filter, RotateCcw } from 'lucide-react';

interface TaskFiltersProps {
  filters: TaskFilterParams;
  onChange: (newFilters: TaskFilterParams) => void;
  onReset: () => void;
  categories?: Category[];
  tags?: Tag[];
}

export const TaskFilters: React.FC<TaskFiltersProps> = ({
  filters,
  onChange,
  onReset,
  categories = [],
  tags = [],
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2.5 p-3.5 bg-slate-900/60 border border-slate-800 rounded-2xl">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mr-1">
        <Filter className="w-3.5 h-3.5 text-emerald-400" />
        <span>Filter:</span>
      </div>

      {/* Status Filter */}
      <select
        value={filters.status || ''}
        onChange={(e) =>
          onChange({
            ...filters,
            status: (e.target.value as TaskStatus) || undefined,
            page: 1,
          })
        }
        className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
      >
        <option value="">All Statuses</option>
        <option value="TODO">Todo</option>
        <option value="IN_PROGRESS">In Progress</option>
        <option value="COMPLETED">Completed</option>
        <option value="CANCELLED">Cancelled</option>
      </select>

      {/* Priority Filter */}
      <select
        value={filters.priority || ''}
        onChange={(e) =>
          onChange({
            ...filters,
            priority: (e.target.value as TaskPriority) || undefined,
            page: 1,
          })
        }
        className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
      >
        <option value="">All Priorities</option>
        <option value="LOW">Low</option>
        <option value="MEDIUM">Medium</option>
        <option value="HIGH">High</option>
        <option value="URGENT">Urgent</option>
      </select>

      {/* Category Filter */}
      {categories.length > 0 && (
        <select
          value={filters.category_id || ''}
          onChange={(e) =>
            onChange({
              ...filters,
              category_id: e.target.value || undefined,
              page: 1,
            })
          }
          className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
      )}

      {/* Tag Filter */}
      {tags.length > 0 && (
        <select
          value={filters.tag_id || ''}
          onChange={(e) =>
            onChange({
              ...filters,
              tag_id: e.target.value || undefined,
              page: 1,
            })
          }
          className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
        >
          <option value="">All Tags</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id}>
              #{t.name}
            </option>
          ))}
        </select>
      )}

      {/* Archived Filter */}
      <select
        value={filters.is_archived ? 'true' : 'false'}
        onChange={(e) =>
          onChange({
            ...filters,
            is_archived: e.target.value === 'true',
            page: 1,
          })
        }
        className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
      >
        <option value="false">Active Tasks</option>
        <option value="true">Archived Tasks</option>
      </select>

      {/* Sort By */}
      <div className="flex items-center gap-1.5 ml-auto">
        <span className="text-xs text-slate-400">Sort:</span>
        <select
          value={filters.sort_by || 'created_at'}
          onChange={(e) =>
            onChange({
              ...filters,
              sort_by: e.target.value as TaskFilterParams['sort_by'],
              page: 1,
            })
          }
          className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
        >
          <option value="created_at">Date Created</option>
          <option value="due_date">Due Date</option>
          <option value="priority">Priority</option>
          <option value="status">Status</option>
          <option value="title">Title</option>
        </select>

        <select
          value={filters.sort_order || 'desc'}
          onChange={(e) =>
            onChange({
              ...filters,
              sort_order: e.target.value as 'asc' | 'desc',
              page: 1,
            })
          }
          className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-xs outline-none focus:border-emerald-500 transition"
        >
          <option value="desc">Desc</option>
          <option value="asc">Asc</option>
        </select>

        <button
          onClick={onReset}
          title="Reset filters"
          className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
