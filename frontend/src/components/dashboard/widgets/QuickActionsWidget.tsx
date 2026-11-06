import React from 'react';
import { Link } from 'react-router-dom';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { CheckSquare, FolderPlus, Repeat, BarChart3 } from 'lucide-react';

export const QuickActionsWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  return (
    <WidgetContainer
      title="Quick Actions"
      description="Direct workspace shortcuts"
      size={widgetConfig.size}
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link
          to="/tasks"
          className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-emerald-500/40 hover:bg-emerald-500/5 transition text-center group"
        >
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-2 group-hover:scale-105 transition">
            <CheckSquare className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-200 group-hover:text-emerald-300 transition">
            Create Task
          </span>
          <span className="text-[10px] text-slate-500 mt-0.5">Manage tasks</span>
        </Link>

        <Link
          to="/projects"
          className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-blue-500/40 hover:bg-blue-500/5 transition text-center group"
        >
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-2 group-hover:scale-105 transition">
            <FolderPlus className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-300 transition">
            New Project
          </span>
          <span className="text-[10px] text-slate-500 mt-0.5">Organize items</span>
        </Link>

        <Link
          to="/recurring-tasks"
          className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-purple-500/40 hover:bg-purple-500/5 transition text-center group"
        >
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-2 group-hover:scale-105 transition">
            <Repeat className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-200 group-hover:text-purple-300 transition">
            Recurring Series
          </span>
          <span className="text-[10px] text-slate-500 mt-0.5">Automate routines</span>
        </Link>

        <Link
          to="/analytics"
          className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-teal-500/40 hover:bg-teal-500/5 transition text-center group"
        >
          <div className="w-9 h-9 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-2 group-hover:scale-105 transition">
            <BarChart3 className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-200 group-hover:text-teal-300 transition">
            Analytics
          </span>
          <span className="text-[10px] text-slate-500 mt-0.5">Review insights</span>
        </Link>
      </div>
    </WidgetContainer>
  );
};
