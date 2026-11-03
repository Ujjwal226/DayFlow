import React, { useState } from 'react';
import { useProjects } from '../hooks/useProjects';
import { Project } from '../types/project';
import { ProjectCard } from '../components/projects/ProjectCard';
import { ProjectFilters } from '../components/projects/ProjectFilters';
import { ProjectForm } from '../components/projects/ProjectForm';

export const ProjectsPage: React.FC = () => {
  const {
    projects,
    total,
    page,
    totalPages,
    isLoading,
    error,
    search,
    setSearch,
    status,
    setStatus,
    priority,
    setPriority,
    isArchived,
    setIsArchived,
    setPage,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject,
    resetFilters,
  } = useProjects();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleOpenCreate = () => {
    setEditingProject(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (project: Project) => {
    setEditingProject(project);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProject(null);
  };

  const handleFormSubmit = async (payload: Parameters<typeof createProject>[0]) => {
    setIsSubmitting(true);
    try {
      if (editingProject) {
        await updateProject(editingProject.id, payload);
      } else {
        await createProject(payload);
      }
      handleCloseModal();
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!projectToDelete) return;
    try {
      await deleteProject(projectToDelete);
      setProjectToDelete(null);
    } catch {
      // Error handled by hook
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-sm text-gray-500 mt-1">
            Organize tasks, monitor deadlines, and track milestones.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
        >
          + New Project
        </button>
      </div>

      {/* Filters */}
      <ProjectFilters
        search={search}
        onSearchChange={setSearch}
        status={status}
        onStatusChange={setStatus}
        priority={priority}
        onPriorityChange={setPriority}
        isArchived={isArchived}
        onIsArchivedChange={setIsArchived}
        onReset={resetFilters}
      />

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 bg-gray-100 rounded-xl border border-gray-200" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300 p-6">
          <p className="text-gray-500 text-sm">
            {isArchived
              ? 'No archived projects found.'
              : search || status || priority
              ? 'No projects match your current filters.'
              : 'No projects created yet. Start organizing your work by creating your first project!'}
          </p>
          {!isArchived && (
            <button
              onClick={handleOpenCreate}
              className="mt-4 px-4 py-2 text-xs font-medium text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50"
            >
              Create Project
            </button>
          )}
        </div>
      ) : (
        /* Projects Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onEdit={handleOpenEdit}
              onArchive={archiveProject}
              onRestore={restoreProject}
              onDelete={(id) => setProjectToDelete(id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-4">
          <p className="text-xs text-gray-500">
            Showing page {page} of {totalPages} ({total} total projects)
          </p>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 text-xs border rounded disabled:opacity-50 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 text-xs border rounded disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Project Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl relative animate-in fade-in">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              {editingProject ? 'Edit Project' : 'Create New Project'}
            </h2>
            <ProjectForm
              initialProject={editingProject}
              onSubmit={handleFormSubmit}
              onCancel={handleCloseModal}
              isLoading={isSubmitting}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-gray-900">Delete Project?</h3>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete this project? Your associated tasks will be preserved and unassigned from the project.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setProjectToDelete(null)}
                className="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 text-xs font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
              >
                Delete Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
