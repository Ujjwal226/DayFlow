import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../../../api/projects';
import { Project } from '../../../types/project';
import { WidgetProps } from '../../../types/dashboard';
import { WidgetContainer } from '../WidgetContainer';
import { ArrowRight, FolderKanban } from 'lucide-react';
import { ProjectOverviewSkeleton } from '../WidgetSkeletons';

export const ProjectsOverviewWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await projectsApi.list({ is_archived: false });
      setProjects(res.items.slice(0, 5));
    } catch {
      setError('Unable to load projects.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <WidgetContainer
      title="Projects Overview"
      description="Active projects progress"
      size={widgetConfig.size}
      isLoading={loading}
      skeleton={<ProjectOverviewSkeleton />}
      error={error}
      onRetry={fetchProjects}
      headerAction={
        <Link
          to="/projects"
          className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium transition"
        >
          <span>All Projects</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      {projects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          <FolderKanban className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-medium text-slate-400">No active projects</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Organize related tasks into focused projects</p>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-64 pr-1">
          {projects.map((proj) => {
            const stats = proj.statistics;
            const total = stats?.total_tasks ?? 0;
            const completed = stats?.completed_tasks ?? 0;
            const progress = stats?.completion_percentage ?? (total > 0 ? Math.round((completed / total) * 100) : 0);

            return (
              <Link
                key={proj.id}
                to={`/projects/${proj.id}`}
                className="block p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-950 transition group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: proj.color || '#3b82f6' }}
                    />
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition truncate">
                      {proj.name}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-slate-300 shrink-0">
                    {progress}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>

                <div className="flex items-center justify-between mt-2 text-[10px] text-slate-400">
                  <span>
                    {completed} of {total} tasks
                  </span>
                  <span className="capitalize">{proj.status.toLowerCase().replace('_', ' ')}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </WidgetContainer>
  );
};
