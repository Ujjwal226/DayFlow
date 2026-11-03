import { useState, useEffect, useCallback } from 'react';
import { tasksApi } from '../api/tasks';
import {
  Task,
  TaskCreatePayload,
  TaskFilterParams,
  TaskListResponse,
  TaskStatistics,
  TaskUpdatePayload,
} from '../types/task';

export const useTasks = (initialFilters: TaskFilterParams = {}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);

  const [filters, setFilters] = useState<TaskFilterParams>({
    page: 1,
    page_size: 20,
    is_archived: false,
    sort_by: 'created_at',
    sort_order: 'desc',
    ...initialFilters,
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data: TaskListResponse = await tasksApi.listTasks(filters);
      setTasks(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch tasks.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await tasksApi.getStatistics();
      setStatistics(stats);
    } catch {
      // Non-fatal if statistics fail
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchStatistics();
  }, [fetchTasks, fetchStatistics]);

  const createTask = async (payload: TaskCreatePayload) => {
    const created = await tasksApi.createTask(payload);
    await Promise.all([fetchTasks(), fetchStatistics()]);
    return created;
  };

  const updateTask = async (taskId: string, payload: TaskUpdatePayload) => {
    const updated = await tasksApi.updateTask(taskId, payload);
    await Promise.all([fetchTasks(), fetchStatistics()]);
    return updated;
  };

  const deleteTask = async (taskId: string) => {
    await tasksApi.deleteTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics()]);
  };

  const duplicateTask = async (taskId: string) => {
    const duplicated = await tasksApi.duplicateTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics()]);
    return duplicated;
  };

  const archiveTask = async (taskId: string) => {
    const archived = await tasksApi.archiveTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics()]);
    return archived;
  };

  const restoreTask = async (taskId: string) => {
    const restored = await tasksApi.restoreTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics()]);
    return restored;
  };

  return {
    tasks,
    total,
    totalPages,
    statistics,
    filters,
    setFilters,
    isLoading,
    error,
    refreshTasks: fetchTasks,
    refreshStatistics: fetchStatistics,
    createTask,
    updateTask,
    deleteTask,
    duplicateTask,
    archiveTask,
    restoreTask,
  };
};

