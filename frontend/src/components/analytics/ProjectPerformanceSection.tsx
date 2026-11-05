import React from 'react';
import { FolderKanban, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { ProjectAnalyticsResponse } from '../../types/analytics';

interface ProjectPerformanceSectionProps {
  projectsData: ProjectAnalyticsResponse | null;
  loading: boolean;
}

export const ProjectPerformanceSection: React.FC<ProjectPerformanceSectionProps> = ({
  projectsData,
  loading,
}) => {
  if (loading && !projectsData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-56 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading project performance...</span>
      </div>
    );
  }

  const projects = projectsData?.projects || [];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <FolderKanban className="w-4 h-4 text-emerald-400" />
            <span>Project Performance</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
              {projects.length} {projects.length === 1 ? 'project' : 'projects'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Root task distribution, completion rates, and active overdues per project.
          </p>
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="p-8 rounded-xl border border-dashed border-slate-800 text-center space-y-1">
          <p className="text-sm font-medium text-slate-400">No projects found</p>
          <p className="text-xs text-slate-500">
            Create projects and assign tasks to track project-level completion rates.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          {projects.map((proj) => {
            const hasOverdue = proj.overdue_tasks > 0;
            return (
              <div
                key={proj.project_id}
                className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition space-y-3"
              >
                {/* Project Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{
                        backgroundColor: proj.project_color || '#10b981',
                      }}
                    />
                    <span className="text-sm font-semibold text-white truncate">
                      {proj.project_name}
                    </span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 capitalize shrink-0">
                    {proj.project_status.toLowerCase()}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Progress</span>
                    <span className="text-white font-medium">
                      {proj.completion_percentage}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
                      style={{ width: `${Math.min(proj.completion_percentage, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Metric Badges */}
                <div className="grid grid-cols-4 gap-2 text-center text-xs pt-1 border-t border-slate-800/60">
                  <div className="py-1">
                    <span className="text-[10px] text-slate-500 block uppercase">Total</span>
                    <span className="font-semibold text-slate-200">{proj.total_tasks}</span>
                  </div>
                  <div className="py-1">
                    <span className="text-[10px] text-emerald-400/80 block uppercase flex items-center justify-center gap-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5" /> Done
                    </span>
                    <span className="font-semibold text-emerald-400">{proj.completed_tasks}</span>
                  </div>
                  <div className="py-1">
                    <span className="text-[10px] text-amber-400/80 block uppercase flex items-center justify-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" /> Todo
                    </span>
                    <span className="font-semibold text-amber-400">{proj.pending_tasks}</span>
                  </div>
                  <div className="py-1">
                    <span
                      className={`text-[10px] block uppercase flex items-center justify-center gap-0.5 ${
                        hasOverdue ? 'text-rose-400' : 'text-slate-500'
                      }`}
                    >
                      <AlertTriangle className="w-2.5 h-2.5" /> Overdue
                    </span>
                    <span
                      className={`font-semibold ${
                        hasOverdue ? 'text-rose-400' : 'text-slate-400'
                      }`}
                    >
                      {proj.overdue_tasks}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

