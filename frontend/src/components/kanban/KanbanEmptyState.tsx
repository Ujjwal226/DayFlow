import React from 'react';
import { TaskStatus } from '../../types/task';
import { CheckCircle2, Inbox, Plus } from 'lucide-react';

interface KanbanEmptyStateProps {
  status: TaskStatus;
  onAddTask?: (status: TaskStatus) => void;
}

export const KanbanEmptyState: React.FC<KanbanEmptyStateProps> = ({ status, onAddTask }) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 text-center border-2 border-dashed border-slate-800/80 rounded-xl bg-slate-900/20 my-2">
      {status === 'COMPLETED' ? (
        <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mb-2" />
      ) : (
        <Inbox className="w-8 h-8 text-slate-600 mb-2" />
      )}
      <p className="text-xs font-medium text-slate-400">No tasks here</p>
      <p className="text-[11px] text-slate-500 mt-0.5">Drag tasks or create a new one</p>

      {onAddTask && (
        <button
          onClick={() => onAddTask(status)}
          className="mt-3 flex items-center gap-1 text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add task</span>
        </button>
      )}
    </div>
  );
};

