import React from 'react';
import { Link } from 'react-router-dom';
import { Project } from '../../types/project';
import { ProjectStatusBadge } from './ProjectStatusBadge';
import { ProjectPriorityBadge } from './ProjectPriorityBadge';
import { ProjectProgress } from './ProjectProgress';

interface ProjectCardProps {
  project: Project;
  onEdit: (project: Project) => void;
  onArchive: (id: string) => void;
  onRestore: (id: string) => void;
  onDelete: (id: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onEdit,
  onArchive,
  onRestore,
  onDelete,
}) => {
  const stats = project.statistics || {
    total_tasks: 0,
    completed_tasks: 0,
    completion_percentage: 0,
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col justify-between">
      <div>
        {/* Top bar: color pill, badges, actions */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            {project.color && (
              <span
                className="w-3.5 h-3.5 rounded-full inline-block border border-black/10 shrink-0"
                style={{ backgroundColor: project.color }}
              />
            )}
            <ProjectStatusBadge status={project.status} />
            <ProjectPriorityBadge priority={project.priority} />
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => onEdit(project)}
              className="text-xs text-gray-500 hover:text-blue-600 px-2 py-1 rounded hover:bg-gray-50"
              title="Edit project"
            >
              Edit
            </button>
            {project.is_archived ? (
              <button
                onClick={() => onRestore(project.id)}
                className="text-xs text-emerald-600 hover:text-emerald-700 px-2 py-1 rounded hover:bg-emerald-50"
                title="Restore project"
              >
                Restore
              </button>
            ) : (
              <button
                onClick={() => onArchive(project.id)}
                className="text-xs text-amber-600 hover:text-amber-700 px-2 py-1 rounded hover:bg-amber-50"
                title="Archive project"
              >
                Archive
              </button>
            )}
            <button
              onClick={() => onDelete(project.id)}
              className="text-xs text-red-600 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
              title="Delete project"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Title & Description */}
        <Link
          to={`/projects/${project.id}`}
          className="block group"
        >
          <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
            {project.name}
          </h3>
        </Link>
        {project.description && (
          <p className="text-xs text-gray-600 mt-1 line-clamp-2">
            {project.description}
          </p>
        )}

        {/* Timeline Dates */}
        {(project.start_date || project.due_date) && (
          <div className="mt-3 text-xs text-gray-500 flex items-center gap-2">
            <span>
              {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Immediate'}
              {' — '}
              {project.due_date ? new Date(project.due_date).toLocaleDateString() : 'No deadline'}
            </span>
          </div>
        )}
      </div>

      {/* Bottom Progress */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <ProjectProgress
          completed={stats.completed_tasks}
          total={stats.total_tasks}
          percentage={stats.completion_percentage}
        />
      </div>
    </div>
  );
};

