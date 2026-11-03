import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { projectsApi, ProjectTaskFilterParams } from '../api/projects';
import { tasksApi } from '../api/tasks';
import { Project, ProjectStatistics } from '../types/project';
import { Task, TaskPriority, TaskStatus } from '../types/task';
import { ProjectStatusBadge } from '../components/projects/ProjectStatusBadge';
import { ProjectPriorityBadge } from '../components/projects/ProjectPriorityBadge';
import { ProjectProgress } from '../components/projects/ProjectProgress';
import { ProjectStatisticsView } from '../components/projects/ProjectStatistics';
import { ProjectForm } from '../components/projects/ProjectForm';

export const ProjectDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStatistics | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [totalTasks, setTotalTasks] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(0);

  // Filters for project tasks
  const [taskSearch, setTaskSearch] = useState('');
  const [taskStatus, setTaskStatus] = useState<TaskStatus | ''>('');
  const [taskPriority, setTaskPriority] = useState<TaskPriority | ''>('');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [availableTasks, setAvailableTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjectData = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [projData, statsData] = await Promise.all([
        projectsApi.get(id),
        projectsApi.getStatistics(id),
      ]);
      setProject(projData);
      setStats(statsData);

      const params: ProjectTaskFilterParams = {
        search: taskSearch.trim() || undefined,
        status: taskStatus || undefined,
        priority: taskPriority || undefined,
        page,
        page_size: pageSize,
      };
      const tasksData = await projectsApi.listTasks(id, params);
      setTasks(tasksData.items);
      setTotalTasks(tasksData.total);
      setTotalPages(tasksData.total_pages);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load project details.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [id, taskSearch, taskStatus, taskPriority, page, pageSize]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  // Load unassigned or eligible tasks for the assignment modal
  const handleOpenAssignModal = async () => {
    if (!id) return;
    try {
      const res = await tasksApi.listTasks({ is_archived: false, page_size: 100 });
      // Filter out tasks already assigned to this project or subtasks
      const assignable = res.items.filter(
        (t: Task) => t.project_id !== id && !t.parent_task_id
      );
      setAvailableTasks(assignable);
      if (assignable.length > 0) {
        setSelectedTaskId(assignable[0].id);
      }
      setIsAssignModalOpen(true);
    } catch {
      // Error loading tasks
    }
  };

  const handleAssignTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !selectedTaskId) return;
    setIsSubmitting(true);
    try {
      await projectsApi.assignTask(id, selectedTaskId);
      setIsAssignModalOpen(false);
      setSelectedTaskId('');
      await fetchProjectData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemoveTask = async (taskId: string) => {
    if (!id) return;
    try {
      await projectsApi.removeTask(id, taskId);
      await fetchProjectData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      }
    }
  };

  const handleUpdateProject = async (payload: Parameters<typeof projectsApi.update>[1]) => {
    if (!id) return;
    setIsSubmitting(true);
    try {
      await projectsApi.update(id, payload);
      setIsEditModalOpen(false);
      await fetchProjectData();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!id) return;
    if (window.confirm('Delete this project? Associated tasks will be preserved.')) {
      await projectsApi.delete(id);
      navigate('/projects');
    }
  };

  if (isLoading && !project) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="h-24 bg-gray-100 rounded-xl" />
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm mb-4">
          {error}
        </div>
        <Link to="/projects" className="text-sm text-blue-600 hover:underline">
          &larr; Back to Projects
        </Link>
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button & header */}
      <div>
        <Link to="/projects" className="text-xs text-gray-500 hover:text-gray-800 flex items-center gap-1 mb-3">
          &larr; Back to Projects
        </Link>

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              {project.color && (
                <span
                  className="w-4 h-4 rounded-full inline-block border border-black/10 shrink-0"
                  style={{ backgroundColor: project.color }}
                />
              )}
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              <ProjectStatusBadge status={project.status} />
              <ProjectPriorityBadge priority={project.priority} />
              {project.is_archived && (
                <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded">
                  Archived
                </span>
              )}
            </div>

            {project.description && (
              <p className="text-sm text-gray-600 max-w-2xl">{project.description}</p>
            )}

            {(project.start_date || project.due_date) && (
              <div className="text-xs text-gray-500 flex items-center gap-4 pt-1">
                <span>Start: {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Immediate'}</span>
                <span>Deadline: {project.due_date ? new Date(project.due_date).toLocaleDateString() : 'None'}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Edit Project
            </button>
            <button
              onClick={handleDeleteProject}
              className="px-3 py-1.5 text-xs font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Statistics & Progress */}
      {stats && (
        <div className="space-y-4">
          <ProjectStatisticsView statistics={stats} />
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <ProjectProgress
              completed={stats.completed_tasks}
              total={stats.total_tasks}
              percentage={stats.completion_percentage}
            />
          </div>
        </div>
      )}

      {/* Project Tasks Section */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Project Tasks</h2>
            <p className="text-xs text-gray-500">
              Tasks assigned directly to this project ({totalTasks} total)
            </p>
          </div>

          <button
            onClick={handleOpenAssignModal}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none"
          >
            + Assign Existing Task
          </button>
        </div>

        {/* Task Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            value={taskSearch}
            onChange={(e) => setTaskSearch(e.target.value)}
            placeholder="Search project tasks..."
            className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <select
            value={taskStatus}
            onChange={(e) => setTaskStatus(e.target.value as TaskStatus | '')}
            className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="TODO">To Do</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
          <select
            value={taskPriority}
            onChange={(e) => setTaskPriority(e.target.value as TaskPriority | '')}
            className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>

        {/* Task List Table/Cards */}
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-xs border border-dashed border-gray-200 rounded-lg">
            No tasks currently assigned to this project.
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="py-3 flex items-center justify-between gap-4 hover:bg-gray-50/50 px-2 rounded-lg transition-colors"
              >
                <div className="min-w-0">
                  <Link
                    to={`/tasks/${task.id}`}
                    className="text-sm font-medium text-gray-900 hover:text-blue-600 truncate block"
                  >
                    {task.title}
                  </Link>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    <span className="font-semibold text-gray-700">{task.status}</span>
                    <span>•</span>
                    <span>{task.priority}</span>
                    {task.due_date && (
                      <>
                        <span>•</span>
                        <span>Due {new Date(task.due_date).toLocaleDateString()}</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to={`/tasks/${task.id}`}
                    className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border border-gray-200"
                  >
                    View
                  </Link>
                  <button
                    onClick={() => handleRemoveTask(task.id)}
                    className="text-xs text-red-600 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
                    title="Remove from project"
                  >
                    Unassign
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center pt-3 border-t border-gray-100 text-xs text-gray-500">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-2 py-1 border rounded disabled:opacity-50"
              >
                Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="px-2 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl relative animate-in fade-in">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Edit Project</h2>
            <ProjectForm
              initialProject={project}
              onSubmit={handleUpdateProject}
              onCancel={() => setIsEditModalOpen(false)}
              isLoading={isSubmitting}
            />
          </div>
        </div>
      )}

      {/* Assign Task Modal */}
      {isAssignModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-gray-900">Assign Task to Project</h3>
            {availableTasks.length === 0 ? (
              <p className="text-xs text-gray-500">
                No unassigned top-level tasks available to add.
              </p>
            ) : (
              <form onSubmit={handleAssignTask} className="space-y-4">
                <div>
                  <label htmlFor="task-select" className="block text-xs font-medium text-gray-700 mb-1">
                    Select Task
                  </label>
                  <select
                    id="task-select"
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {availableTasks.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title} ({t.status})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsAssignModalOpen(false)}
                    className="px-3 py-1.5 text-xs text-gray-700 border rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-3 py-1.5 text-xs text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                  >
                    {isSubmitting ? 'Assigning...' : 'Assign Task'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
