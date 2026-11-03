import React from 'react';
import { ProjectPriority } from '../../types/project';

interface ProjectPriorityBadgeProps {
  priority: ProjectPriority;
  className?: string;
}

export const ProjectPriorityBadge: React.FC<ProjectPriorityBadgeProps> = ({ priority, className = '' }) => {
  const getBadgeStyle = () => {
    switch (priority) {
      case 'URGENT':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'MEDIUM':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'LOW':
        return 'bg-slate-50 text-slate-600 border-slate-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const formatPriority = () => {
    switch (priority) {
      case 'URGENT':
        return 'Urgent';
      case 'HIGH':
        return 'High';
      case 'MEDIUM':
        return 'Medium';
      case 'LOW':
        return 'Low';
      default:
        return priority;
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getBadgeStyle()} ${className}`}
    >
      {formatPriority()}
    </span>
  );
};

