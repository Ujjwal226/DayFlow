import { TaskPriority, TaskStatus } from './task';

export interface KanbanFiltersState {
  search: string;
  projectId: string | 'ALL' | 'NO_PROJECT';
  categoryId: string | 'ALL';
  priority: TaskPriority | 'ALL';
  recurringOnly: boolean;
}

export interface KanbanColumnConfig {
  id: TaskStatus;
  title: string;
  accentColor: string;
  badgeBg: string;
  badgeText: string;
  dotColor: string;
}

export const KANBAN_COLUMNS: KanbanColumnConfig[] = [
  {
    id: 'TODO',
    title: 'To Do',
    accentColor: 'border-slate-700/60',
    badgeBg: 'bg-slate-800/80',
    badgeText: 'text-slate-300',
    dotColor: 'bg-slate-400',
  },
  {
    id: 'IN_PROGRESS',
    title: 'In Progress',
    accentColor: 'border-blue-500/30',
    badgeBg: 'bg-blue-500/10',
    badgeText: 'text-blue-400',
    dotColor: 'bg-blue-400',
  },
  {
    id: 'COMPLETED',
    title: 'Completed',
    accentColor: 'border-emerald-500/30',
    badgeBg: 'bg-emerald-500/10',
    badgeText: 'text-emerald-400',
    dotColor: 'bg-emerald-400',
  },
  {
    id: 'CANCELLED',
    title: 'Cancelled',
    accentColor: 'border-rose-500/30',
    badgeBg: 'bg-rose-500/10',
    badgeText: 'text-rose-400',
    dotColor: 'bg-rose-400',
  },
];

