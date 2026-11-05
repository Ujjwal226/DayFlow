import React from 'react';
import { ActivityLog, ActivityAction } from '../../types/activityLog';
import {
  CheckCircle2,
  PlusCircle,
  Edit,
  Trash2,
  FolderKanban,
  Repeat,
  Tag,
  Folder,
  RotateCcw,
  Archive,
  Copy,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface ActivityItemProps {
  activity: ActivityLog;
  compact?: boolean;
}

const getActionDetails = (action: ActivityAction) => {
  switch (action) {
    case 'TASK_CREATED':
      return {
        label: 'Task created',
        icon: PlusCircle,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'TASK_UPDATED':
      return {
        label: 'Task updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'TASK_COMPLETED':
      return {
        label: 'Task completed',
        icon: CheckCircle2,
        color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
      };
    case 'TASK_REOPENED':
      return {
        label: 'Task reopened',
        icon: RotateCcw,
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      };
    case 'TASK_DELETED':
      return {
        label: 'Task deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };
    case 'TASK_ARCHIVED':
      return {
        label: 'Task archived',
        icon: Archive,
        color: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
      };
    case 'TASK_RESTORED':
      return {
        label: 'Task restored',
        icon: RotateCcw,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'TASK_DUPLICATED':
      return {
        label: 'Task duplicated',
        icon: Copy,
        color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
      };

    case 'SUBTASK_CREATED':
      return {
        label: 'Subtask added',
        icon: PlusCircle,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'SUBTASK_UPDATED':
      return {
        label: 'Subtask updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'SUBTASK_COMPLETED':
      return {
        label: 'Subtask completed',
        icon: CheckCircle2,
        color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
      };
    case 'SUBTASK_DELETED':
      return {
        label: 'Subtask deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };

    case 'PROJECT_CREATED':
      return {
        label: 'Project created',
        icon: FolderKanban,
        color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      };
    case 'PROJECT_UPDATED':
      return {
        label: 'Project updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'PROJECT_ARCHIVED':
      return {
        label: 'Project archived',
        icon: Archive,
        color: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
      };
    case 'PROJECT_RESTORED':
      return {
        label: 'Project restored',
        icon: RotateCcw,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'PROJECT_DELETED':
      return {
        label: 'Project deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };

    case 'RECURRING_SERIES_CREATED':
      return {
        label: 'Recurring series created',
        icon: Repeat,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'RECURRING_SERIES_UPDATED':
      return {
        label: 'Recurring series updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'RECURRING_SERIES_PAUSED':
      return {
        label: 'Recurring series paused',
        icon: Clock,
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      };
    case 'RECURRING_SERIES_RESUMED':
      return {
        label: 'Recurring series resumed',
        icon: RotateCcw,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      };
    case 'RECURRING_SERIES_STOPPED':
      return {
        label: 'Recurring series stopped',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };
    case 'RECURRING_SERIES_DELETED':
      return {
        label: 'Recurring series deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };
    case 'RECURRING_OCCURRENCE_GENERATED':
      return {
        label: 'Occurrence generated',
        icon: Repeat,
        color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
      };
    case 'RECURRING_OCCURRENCE_SKIPPED':
      return {
        label: 'Occurrence skipped',
        icon: Clock,
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      };

    case 'CATEGORY_CREATED':
      return {
        label: 'Category created',
        icon: Folder,
        color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
      };
    case 'CATEGORY_UPDATED':
      return {
        label: 'Category updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'CATEGORY_DELETED':
      return {
        label: 'Category deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };

    case 'TAG_CREATED':
      return {
        label: 'Tag created',
        icon: Tag,
        color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
      };
    case 'TAG_UPDATED':
      return {
        label: 'Tag updated',
        icon: Edit,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      };
    case 'TAG_DELETED':
      return {
        label: 'Tag deleted',
        icon: Trash2,
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      };
    case 'TAG_ASSIGNED':
      return {
        label: 'Tag assigned',
        icon: Tag,
        color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
      };
    case 'TAG_REMOVED':
      return {
        label: 'Tag removed',
        icon: Tag,
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      };

    default:
      return {
        label: String(action).replace(/_/g, ' ').toLowerCase(),
        icon: Clock,
        color: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
      };
  }
};

const formatTimestamp = (dateStr: string) => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
};

export const ActivityItem: React.FC<ActivityItemProps> = ({
  activity,
  compact = false,
}) => {
  const details = getActionDetails(activity.action);
  const IconComponent = details.icon;

  const entityTitle =
    (activity.metadata?.title as string) ||
    (activity.metadata?.name as string) ||
    `${activity.entity_type} #${activity.entity_id.substring(0, 8)}`;

  const changesList = activity.changes ? Object.entries(activity.changes) : [];

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-xl border border-slate-800/80 bg-slate-900/60 hover:border-slate-700/80 transition ${
        compact ? 'text-xs' : 'text-sm'
      }`}
    >
      <div
        className={`p-2 rounded-lg border flex-shrink-0 ${details.color}`}
        title={details.label}
      >
        <IconComponent className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-200">
              {details.label}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
              {activity.entity_type}
            </span>
          </div>
          <span className="text-[11px] text-slate-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTimestamp(activity.created_at)}
          </span>
        </div>

        <p className="mt-1 text-slate-300 font-medium truncate">
          {entityTitle}
        </p>

        {changesList.length > 0 && (
          <div className="mt-2 space-y-1 bg-slate-950/60 p-2 rounded-lg border border-slate-800/50 text-xs">
            {changesList.map(([field, delta]) => (
              <div key={field} className="flex items-center gap-2 text-slate-400">
                <span className="font-medium text-slate-300">{field}:</span>
                <span className="line-through text-rose-400/80 truncate max-w-[150px]">
                  {delta.old !== null && delta.old !== undefined
                    ? String(delta.old)
                    : 'empty'}
                </span>
                <ArrowRight className="w-3 h-3 text-slate-500 flex-shrink-0" />
                <span className="text-emerald-400 truncate max-w-[150px]">
                  {delta.new !== null && delta.new !== undefined
                    ? String(delta.new)
                    : 'empty'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

