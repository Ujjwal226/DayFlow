import React, { useState } from 'react';
import { Task, TaskStatus } from '../../types/task';
import { Project } from '../../types/project';
import { KanbanColumnConfig } from '../../types/kanban';
import { KanbanTaskCard } from './KanbanTaskCard';
import { KanbanEmptyState } from './KanbanEmptyState';
import { Plus } from 'lucide-react';

interface KanbanColumnProps {
  config: KanbanColumnConfig;
  tasks: Task[];
  projectsMap: Map<string, Project>;
  onEditTask: (task: Task) => void;
  onDeleteTask: (task: Task) => void;
  onDropTask: (taskId: string, targetStatus: TaskStatus) => void;
  onAddTask: (status: TaskStatus) => void;
  updatingTaskIds: Set<string>;
}

export const KanbanColumn: React.FC<KanbanColumnProps> = ({
  config,
  tasks,
  projectsMap,
  onEditTask,
  onDeleteTask,
  onDropTask,
  onAddTask,
  updatingTaskIds,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (!isDragOver) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    // Only remove drag over styling if leaving the container itself
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const taskId = e.dataTransfer.getData('text/plain');
    if (taskId) {
      onDropTask(taskId, config.id);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      aria-label={`${config.title} column with ${tasks.length} tasks`}
      className={`flex flex-col flex-1 min-w-[280px] max-w-full md:max-w-sm rounded-2xl bg-slate-900/50 border transition-all duration-200 overflow-hidden shadow-lg backdrop-blur-sm ${
        isDragOver
          ? 'border-emerald-500 bg-emerald-950/20 ring-2 ring-emerald-500/40 shadow-emerald-950/40'
          : config.accentColor
      }`}
    >
      {/* Column Header */}
      <div className="p-3.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/80">
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${config.dotColor}`} />
          <h3 className="font-semibold text-sm text-slate-100">{config.title}</h3>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${config.badgeBg} ${config.badgeText}`}
          >
            {tasks.length}
          </span>
        </div>

        <button
          onClick={() => onAddTask(config.id)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          title={`Add task to ${config.title}`}
          aria-label={`Add task to ${config.title}`}
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Task List / Drop Zone */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3 min-h-[350px] max-h-[calc(100vh-280px)]">
        {tasks.length === 0 ? (
          <KanbanEmptyState status={config.id} onAddTask={onAddTask} />
        ) : (
          tasks.map((task) => (
            <KanbanTaskCard
              key={task.id}
              task={task}
              project={task.project_id ? projectsMap.get(task.project_id) : null}
              onEdit={onEditTask}
              onDelete={onDeleteTask}
              onStatusChange={onDropTask}
              isUpdating={updatingTaskIds.has(task.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};

