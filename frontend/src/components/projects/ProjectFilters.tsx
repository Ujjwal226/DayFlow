import React from 'react';
import { ProjectPriority, ProjectStatus } from '../../types/project';

interface ProjectFiltersProps {
  search: string;
  onSearchChange: (search: string) => void;
  status: ProjectStatus | '';
  onStatusChange: (status: ProjectStatus | '') => void;
  priority: ProjectPriority | '';
  onPriorityChange: (priority: ProjectPriority | '') => void;
  isArchived: boolean;
  onIsArchivedChange: (archived: boolean) => void;
  onReset: () => void;
}

export const ProjectFilters: React.FC<ProjectFiltersProps> = ({
  search,
  onSearchChange,
  status,
  onStatusChange,
  priority,
  onPriorityChange,
  isArchived,
  onIsArchivedChange,
  onReset,
}) => {
  return (
    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search */}
        <div>
          <label htmlFor="search-projects" className="block text-xs font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            id="search-projects"
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search projects..."
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Status */}
        <div>
          <label htmlFor="filter-status" className="block text-xs font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id="filter-status"
            value={status}
            onChange={(e) => onStatusChange(e.target.value as ProjectStatus | '')}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="PLANNED">Planned</option>
            <option value="ACTIVE">Active</option>
            <option value="ON_HOLD">On Hold</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>

        {/* Priority */}
        <div>
          <label htmlFor="filter-priority" className="block text-xs font-medium text-gray-700 mb-1">
            Priority
          </label>
          <select
            id="filter-priority"
            value={priority}
            onChange={(e) => onPriorityChange(e.target.value as ProjectPriority | '')}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>

        {/* Toggle Archived & Reset */}
        <div className="flex items-end justify-between gap-2">
          <label className="flex items-center gap-2 cursor-pointer pb-2">
            <input
              type="checkbox"
              checked={isArchived}
              onChange={(e) => onIsArchivedChange(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <span className="text-xs font-medium text-gray-700">Show Archived</span>
          </label>

          <button
            onClick={onReset}
            className="text-xs text-gray-500 hover:text-gray-800 pb-2 underline focus:outline-none"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </div>
  );
};

