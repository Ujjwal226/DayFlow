import React from 'react';
import { ProjectStatistics } from '../../types/project';

interface ProjectStatisticsProps {
  statistics: ProjectStatistics;
  className?: string;
}

export const ProjectStatisticsView: React.FC<ProjectStatisticsProps> = ({ statistics, className = '' }) => {
  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 ${className}`}>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-gray-500 font-medium">Total Tasks</p>
        <p className="text-xl font-bold text-gray-900 mt-1">{statistics.total_tasks}</p>
      </div>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-emerald-600 font-medium">Completed</p>
        <p className="text-xl font-bold text-emerald-700 mt-1">{statistics.completed_tasks}</p>
      </div>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-blue-600 font-medium">In Progress</p>
        <p className="text-xl font-bold text-blue-700 mt-1">{statistics.in_progress_tasks}</p>
      </div>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-amber-600 font-medium">Pending</p>
        <p className="text-xl font-bold text-amber-700 mt-1">{statistics.pending_tasks}</p>
      </div>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-red-600 font-medium">Overdue</p>
        <p className="text-xl font-bold text-red-700 mt-1">{statistics.overdue_tasks}</p>
      </div>
      <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
        <p className="text-xs text-indigo-600 font-medium">Completion</p>
        <p className="text-xl font-bold text-indigo-700 mt-1">{statistics.completion_percentage}%</p>
      </div>
    </div>
  );
};

