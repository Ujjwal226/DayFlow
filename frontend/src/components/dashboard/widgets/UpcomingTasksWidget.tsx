import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { tasksApi } from '../../../api/tasks';
import { Task } from '../../../types/task';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { TaskStatusBadge } from '../../tasks/TaskStatusBadge';
import { TaskPriorityBadge } from '../../tasks/TaskPriorityBadge';
import { Calendar, ArrowRight } from 'lucide-react';
import { TaskListSkeleton } from '../WidgetSkeletons';

export const UpcomingTasksWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUpcomingTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const now = new Date();
      // Tomorrow start
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowStr = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(tomorrow.getDate()).padStart(2, '0')}`;
      const startOfTomorrow = `${tomorrowStr}T00:00:00`;

      // 7 days ahead
      const nextWeek = new Date(now);
      nextWeek.setDate(nextWeek.getDate() + 7);
      const nextWeekStr = `${nextWeek.getFullYear()}-${String(nextWeek.getMonth() + 1).padStart(2, '0')}-${String(nextWeek.getDate()).padStart(2, '0')}`;
      const endOfNextWeek = `${nextWeekStr}T23:59:59`;

      const res = await tasksApi.listTasks({
        due_date_from: startOfTomorrow,
        due_date_to: endOfNextWeek,
        is_archived: false,
        page: 1,
        page_size: 10,
        sort_by: 'due_date',
        sort_order: 'asc',
      });
      setTasks(res.items);
    } catch {
      setError('Unable to load upcoming tasks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUpcomingTasks();
  }, []);

  return (
    <WidgetContainer
      title="Upcoming Tasks"
      description="Next 7 days schedule"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<TaskListSkeleton />}
      error={error}
      onRetry={fetchUpcomingTasks}
      headerAction={
        <Link
          to="/tasks"
          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition"
        >
          <span>View all</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {tasks.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <Calendar className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-medium text-slate-400">No upcoming tasks scheduled</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Plan ahead by adding due dates to tasks</p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-64 pr-1">
          {tasks.map((task) => (
            <Link
              key={task.id}
              to={`/tasks/${task.id}`}
              className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-950 transition group"
            >
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    task.status === 'COMPLETED' ? 'bg-emerald-500' : 'bg-blue-400'
                  }`}
                />
                <div className="min-w-0">
                  <div
                    className={`text-xs text-slate-200 group-hover:text-emerald-400 transition truncate ${
                      task.status === 'COMPLETED' ? 'line-through text-slate-500' : ''
                    }`}
                  >
                    {task.title}
                  </div>
                  {task.due_date && (
                    <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      <span>{new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <TaskStatusBadge status={task.status} />
                <TaskPriorityBadge priority={task.priority} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </WidgetContainer>
  );
};

