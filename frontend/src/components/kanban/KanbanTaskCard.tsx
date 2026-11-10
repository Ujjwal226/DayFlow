import React from 'react';
import { Task, TaskPriority, TaskStatus } from '../../types/task';
import { Project } from '../../types/project';
import {
  AlertTriangle,
  Repeat,
  Trash2,
  Edit2,
  Clock,
  Layers,
  Folder,
} from 'lucide-react';

interface KanbanTaskCardProps {
  task: Task;
  project?: Project | null;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
  onStatusChange: (taskId: string, newStatus: TaskStatus) => void;
  isUpdating?: boolean;
}

const PRIORITY_CONFIG: Record<
  TaskPriority,
  { label: string; bg: string; text: string; border: string }
> = {
  LOW: {
    label: 'Low',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
  },
  MEDIUM: {
    label: 'Medium',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
  },
  HIGH: {
    label: 'High',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
  },
  URGENT: {
    label: 'Urgent',
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/20',
  },
};

const ALL_STATUSES: { id: TaskStatus; label: string }[] = [
  { id: 'TODO', label: 'To Do' },
  { id: 'IN_PROGRESS', label: 'In Progress' },
  { id: 'COMPLETED', label: 'Completed' },
  { id: 'CANCELLED', label: 'Cancelled' },
];

export const KanbanTaskCard: React.FC<KanbanTaskCardProps> = ({
  task,
  project,
  onEdit,
  onDelete,
  onStatusChange,
  isUpdating = false,
}) => {
  const pConfig = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.MEDIUM;

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('text/plain', task.id);
    e.dataTransfer.effectAllowed = 'move';
    e.currentTarget.classList.add('opacity-50', 'scale-[0.98]');
  };

  const handleDragEnd = (e: React.DragEvent<HTMLDivElement>) => {
    e.currentTarget.classList.remove('opacity-50', 'scale-[0.98]');
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div
      draggable={!isUpdating}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      tabIndex={0}
      aria-label={`Task ${task.title}, priority ${task.priority}, status ${task.status}`}
      className={`group relative rounded-xl border p-4 transition-all duration-200 select-none cursor-grab active:cursor-grabbing focus:outline-none focus:ring-2 focus:ring-emerald-500/50 ${
        isUpdating ? 'opacity-60 pointer-events-none' : ''
      } ${
        task.status === 'COMPLETED'
          ? 'bg-slate-900/40 border-slate-800/80 hover:border-emerald-500/30'
          : task.is_overdue
          ? 'bg-rose-950/20 border-rose-500/40 hover:border-rose-500/70 shadow-sm shadow-rose-950/20'
          : task.priority === 'URGENT'
          ? 'bg-amber-950/10 border-amber-500/30 hover:border-amber-500/60'
          : 'bg-slate-900/70 border-slate-800/90 hover:border-slate-700 shadow-sm'
      }`}
    >
      {/* Top Header: Priority Badge, Category Badge & Action Icons */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Priority */}
          <span
            className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${pConfig.bg} ${pConfig.text} ${pConfig.border}`}
          >
            {pConfig.label}
          </span>

          {/* Category */}
          {task.category && (
            <span
              className="px-2 py-0.5 rounded-md text-[10px] font-medium border border-slate-700/60 bg-slate-800/80 text-slate-300"
              style={{
                borderColor: task.category.color ? `${task.category.color}40` : undefined,
                color: task.category.color || undefined,
              }}
            >
              {task.category.name}
            </span>
          )}

          {/* Recurring Indicator */}
          {task.recurring_task_id && (
            <span
              className="p-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20"
              title="Recurring task series occurrence"
            >
              <Repeat className="w-2.5 h-2.5" />
            </span>
          )}
        </div>

        {/* Action Buttons: Edit, Delete */}
        <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(task);
            }}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Edit task"
            aria-label={`Edit task ${task.title}`}
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(task);
            }}
            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            title="Delete task"
            aria-label={`Delete task ${task.title}`}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Task Title */}
      <h4
        onClick={() => onEdit(task)}
        className={`text-sm font-medium mb-1.5 line-clamp-2 cursor-pointer hover:text-emerald-400 transition ${
          task.status === 'COMPLETED' ? 'line-through text-slate-400' : 'text-slate-100'
        }`}
      >
        {task.title}
      </h4>

      {/* Description Preview (if present) */}
      {task.description && (
        <p className="text-xs text-slate-400 line-clamp-2 mb-2 font-normal leading-relaxed">
          {task.description}
        </p>
      )}

      {/* Tags */}
      {task.tags && task.tags.length > 0 && (
        <div className="flex items-center gap-1 flex-wrap mb-2.5">
          {task.tags.map((tg) => (
            <span
              key={tg.id}
              className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/50"
            >
              #{tg.name}
            </span>
          ))}
        </div>
      )}

      {/* Subtask Progress (if present) */}
      {task.progress && task.progress.total_subtasks > 0 && (
        <div className="mb-2.5">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="flex items-center gap-1">
              <Layers className="w-3 h-3 text-slate-500" />
              <span>Subtasks</span>
            </span>
            <span>
              {task.progress.completed_subtasks}/{task.progress.total_subtasks}
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                task.progress.progress_percentage === 100 ? 'bg-emerald-500' : 'bg-emerald-500/70'
              }`}
              style={{ width: `${task.progress.progress_percentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Card Footer: Project Badge & Due Date */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 gap-2">
        {/* Project Name */}
        {project ? (
          <span
            className="flex items-center gap-1 truncate text-slate-300"
            title={`Project: ${project.name}`}
          >
            <Folder className="w-3 h-3 text-emerald-400 shrink-0" />
            <span className="truncate max-w-[120px]">{project.name}</span>
          </span>
        ) : (
          <span />
        )}

        {/* Due Date & Overdue flag */}
        {task.due_date ? (
          <div
            className={`flex items-center gap-1 font-medium ml-auto ${
              task.is_overdue && task.status !== 'COMPLETED'
                ? 'text-rose-400'
                : 'text-slate-400'
            }`}
            title={task.is_overdue ? 'Task is overdue!' : 'Due date'}
          >
            {task.is_overdue && task.status !== 'COMPLETED' ? (
              <AlertTriangle className="w-3 h-3 text-rose-400" />
            ) : (
              <Clock className="w-3 h-3 text-slate-500" />
            )}
            <span>{formatDate(task.due_date)}</span>
          </div>
        ) : null}
      </div>

      {/* Accessible Keyboard Status Changer */}
      <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
        <label htmlFor={`status-select-${task.id}`} className="text-[10px] text-slate-500">
          Move to:
        </label>
        <select
          id={`status-select-${task.id}`}
          value={task.status}
          onChange={(e) => onStatusChange(task.id, e.target.value as TaskStatus)}
          aria-label={`Change status for ${task.title}`}
          className="bg-slate-950 border border-slate-800 text-slate-300 rounded px-1.5 py-0.5 text-[10px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          {ALL_STATUSES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
