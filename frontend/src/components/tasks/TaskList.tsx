import React from 'react';
import { Task } from '../../types/task';
import { TaskCard } from './TaskCard';
import { CheckSquare, Loader2 } from 'lucide-react';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onEdit: (task: Task) => void;
  onDuplicate: (taskId: string) => void;
  onArchiveToggle: (taskId: string, isArchived: boolean) => void;
  onDelete: (taskId: string) => void;
  onCreateClick?: () => void;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  isLoading,
  onEdit,
  onDuplicate,
  onArchiveToggle,
  onDelete,
  onCreateClick,
}) => {
  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
        <span className="text-sm">Loading your tasks...</span>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="py-16 px-6 text-center bg-slate-900/30 border border-slate-800/80 rounded-3xl flex flex-col items-center justify-center">
        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-3 shadow-inner">
          <CheckSquare className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-white">No tasks found</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          There are no tasks matching your current view or filters.
        </p>
        {onCreateClick && (
          <button
            onClick={onCreateClick}
            className="mt-4 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition shadow-lg shadow-emerald-500/20"
          >
            Create Your First Task
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onEdit={onEdit}
          onDuplicate={onDuplicate}
          onArchiveToggle={onArchiveToggle}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};

