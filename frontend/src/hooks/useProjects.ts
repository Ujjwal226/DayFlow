import { useState, useEffect, useCallback } from 'react';
import { projectsApi, ProjectFilterParams } from '../api/projects';
import { Project, ProjectCreatePayload, ProjectPriority, ProjectStatus, ProjectUpdatePayload } from '../types/project';

export const useProjects = (initialParams: ProjectFilterParams = {}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialParams.page || 1);
  const [pageSize, setPageSize] = useState(initialParams.page_size || 20);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState(initialParams.search || '');
  const [status, setStatus] = useState<ProjectStatus | ''>(initialParams.status || '');
  const [priority, setPriority] = useState<ProjectPriority | ''>(initialParams.priority || '');
  const [isArchived, setIsArchived] = useState(initialParams.is_archived || false);
  const [sortBy, setSortBy] = useState(initialParams.sort_by || 'created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(initialParams.sort_order || 'desc');

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectsApi.list({
        search: search.trim() || undefined,
        status: status || undefined,
        priority: priority || undefined,
        is_archived: isArchived,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      });
      setProjects(data.items);
      setTotal(data.total);
      setPage(data.page);
      setPageSize(data.page_size);
      setTotalPages(data.total_pages);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch projects.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [search, status, priority, isArchived, sortBy, sortOrder, page, pageSize]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const createProject = async (payload: ProjectCreatePayload): Promise<Project> => {
    const created = await projectsApi.create(payload);
    await fetchProjects();
    return created;
  };

  const updateProject = async (id: string, payload: ProjectUpdatePayload): Promise<Project> => {
    const updated = await projectsApi.update(id, payload);
    await fetchProjects();
    return updated;
  };

  const deleteProject = async (id: string): Promise<void> => {
    await projectsApi.delete(id);
    await fetchProjects();
  };

  const archiveProject = async (id: string): Promise<Project> => {
    const archived = await projectsApi.archive(id);
    await fetchProjects();
    return archived;
  };

  const restoreProject = async (id: string): Promise<Project> => {
    const restored = await projectsApi.restore(id);
    await fetchProjects();
    return restored;
  };

  const resetFilters = () => {
    setSearch('');
    setStatus('');
    setPriority('');
    setIsArchived(false);
    setSortBy('created_at');
    setSortOrder('desc');
    setPage(1);
  };

  return {
    projects,
    total,
    page,
    pageSize,
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
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    setPage,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject,
    resetFilters,
  };
};
