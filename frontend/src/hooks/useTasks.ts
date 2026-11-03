import { useState, useEffect, useCallback } from 'react';
import { tasksApi } from '../api/tasks';
import { categoriesApi } from '../api/categories';
import { tagsApi } from '../api/tags';
import {
  Task,
  TaskCreatePayload,
  TaskFilterParams,
  TaskListResponse,
  TaskStatistics,
  TaskUpdatePayload,
} from '../types/task';
import { Category, CategoryCreatePayload } from '../types/category';
import { Tag, TagCreatePayload } from '../types/tag';

export const useTasks = (initialFilters: TaskFilterParams = {}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

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

  const fetchCategories = useCallback(async () => {
    try {
      const cats = await categoriesApi.listCategories();
      setCategories(cats);
    } catch {
      // Non-fatal
    }
  }, []);

  const fetchTags = useCallback(async () => {
    try {
      const t = await tagsApi.listTags();
      setTags(t);
    } catch {
      // Non-fatal
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchStatistics();
    fetchCategories();
    fetchTags();
  }, [fetchTasks, fetchStatistics, fetchCategories, fetchTags]);

  const createTask = async (payload: TaskCreatePayload) => {
    const created = await tasksApi.createTask(payload);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
    return created;
  };

  const updateTask = async (taskId: string, payload: TaskUpdatePayload) => {
    const updated = await tasksApi.updateTask(taskId, payload);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
    return updated;
  };

  const deleteTask = async (taskId: string) => {
    await tasksApi.deleteTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
  };

  const duplicateTask = async (taskId: string) => {
    const duplicated = await tasksApi.duplicateTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
    return duplicated;
  };

  const archiveTask = async (taskId: string) => {
    const archived = await tasksApi.archiveTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
    return archived;
  };

  const restoreTask = async (taskId: string) => {
    const restored = await tasksApi.restoreTask(taskId);
    await Promise.all([fetchTasks(), fetchStatistics(), fetchCategories(), fetchTags()]);
    return restored;
  };

  const createCategory = async (payload: CategoryCreatePayload) => {
    const created = await categoriesApi.createCategory(payload);
    await fetchCategories();
    return created;
  };

  const deleteCategory = async (categoryId: string) => {
    await categoriesApi.deleteCategory(categoryId);
    await Promise.all([fetchCategories(), fetchTasks()]);
  };

  const createTag = async (payload: TagCreatePayload) => {
    const created = await tagsApi.createTag(payload);
    await fetchTags();
    return created;
  };

  const deleteTag = async (tagId: string) => {
    await tagsApi.deleteTag(tagId);
    await Promise.all([fetchTags(), fetchTasks()]);
  };

  return {
    tasks,
    total,
    totalPages,
    statistics,
    categories,
    tags,
    filters,
    setFilters,
    isLoading,
    error,
    refreshTasks: fetchTasks,
    refreshStatistics: fetchStatistics,
    refreshCategories: fetchCategories,
    refreshTags: fetchTags,
    createTask,
    updateTask,
    deleteTask,
    duplicateTask,
    archiveTask,
    restoreTask,
    createCategory,
    deleteCategory,
    createTag,
    deleteTag,
  };
};
