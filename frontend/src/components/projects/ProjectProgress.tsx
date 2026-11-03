import React from 'react';

interface ProjectProgressProps {
  completed: number;
  total: number;
  percentage: number;
  className?: string;
  showCounts?: boolean;
}

export const ProjectProgress: React.FC<ProjectProgressProps> = ({
  completed,
  total,
  percentage,
  className = '',
  showCounts = true,
}) => {
  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
        <span className="font-medium text-gray-700">Project Progress</span>
        <span>
          {showCounts && (
            <span className="mr-1.5 text-gray-500">
              {completed} of {total} tasks
            </span>
          )}
          <span className="font-semibold text-gray-900">{percentage}%</span>
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          className={`h-2 rounded-full transition-all duration-300 ${
            percentage === 100
              ? 'bg-emerald-500'
              : percentage >= 50
              ? 'bg-blue-600'
              : 'bg-amber-500'
          }`}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
      </div>
    </div>
  );
};

