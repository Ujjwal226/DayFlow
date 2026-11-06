import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { tasksApi } from '../../../api/tasks';
import { Task } from '../../../types/task';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { TaskPriorityBadge } from '../../tasks/TaskPriorityBadge';
import { AlertTriangle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { TaskListSkeleton } from '../WidgetSkeletons';

export const OverdueTasksWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverdueTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      // Overdue means due before now and incomplete (TODO or IN_PROGRESS)
      const nowIso = new Date().toISOString();
      const [todoRes, inProgRes] = await Promise.all([
        tasksApi.listTasks({
          status: 'TODO',
          due_date_to: nowIso,
          is_archived: false,
          page: 1,
          page_size: 10,
          sort_by: 'due_date',
          sort_order: 'asc',
        }),
        tasksApi.listTasks({
          status: 'IN_PROGRESS',
          due_date_to: nowIso,
          is_archived: false,
          page: 1,
          page_size: 10,
          sort_by: 'due_date',
          sort_order: 'asc',
        }),
      ]);

      const combined = [...todoRes.items, ...inProgRes.items]
        .filter((t) => t.is_overdue)
        .sort((a, b) => {
          if (!a.due_date) return 1;
          if (!b.due_date) return -1;
          return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
        })
        .slice(0, 10);

      setTasks(combined);
    } catch {
      setError('Unable to load overdue tasks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverdueTasks();
  }, []);

  return (
    <WidgetContainer
      title="Overdue Tasks"
      description="Items requiring immediate attention"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<TaskListSkeleton />}
      error={error}
      onRetry={fetchOverdueTasks}
      headerAction={
        <Link
          to="/tasks"
          className="inline-flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 font-medium transition"
        >
          <span>Resolve</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {tasks.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <CheckCircle2 className="w-8 h-8 text-emerald-400/60 mb-2" />
          <p className="text-xs font-medium text-emerald-300">Zero overdue items</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Great job keeping on top of your deadlines!</p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-64 pr-1">
          {tasks.map((task) => (
            <Link
              key={task.id}
              to={`/tasks/${task.id}`}
              className="flex items-center justify-between p-2.5 rounded-xl bg-rose-500/5 border border-rose-500/20 hover:border-rose-500/40 hover:bg-rose-500/10 transition group"
            >
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs text-slate-200 group-hover:text-rose-300 transition truncate font-medium">
                    {task.title}
                  </div>
                  {task.due_date && (
                    <div className="text-[10px] text-rose-400/80 mt-0.5">
                      Due {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0">
                <TaskPriorityBadge priority={task.priority} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};

