import React from 'react';
import { SubtaskProgress as ISubtaskProgress } from '../../types/subtask';

interface SubtaskProgressProps {
  progress?: ISubtaskProgress;
}

export const SubtaskProgress: React.FC<SubtaskProgressProps> = ({ progress }) => {
  if (!progress || progress.total_subtasks === 0) {
    return null;
  }

  const { total_subtasks, completed_subtasks, progress_percentage } = progress;

  return (
    <div className="w-full">
      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
        <span>Subtasks</span>
        <span>
          {completed_subtasks}/{total_subtasks} ({progress_percentage}%)
        </span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            progress_percentage === 100 ? 'bg-emerald-500' : 'bg-teal-500'
          }`}
          style={{ width: `${progress_percentage}%` }}
        />
      </div>
    </div>
  );
};

