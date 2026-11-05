import { useState, useEffect, useCallback } from 'react';
import { recurringTasksApi } from '../api/recurringTasks';
import {
  RecurringTask,
  RecurringTaskCreatePayload,
  RecurringTaskUpdatePayload,
  RecurringTaskSkipPayload,
  RecurringTaskFilterParams,
  RecurrenceFrequency,
} from '../types/recurringTask';

export const useRecurringTasks = (initialParams?: RecurringTaskFilterParams) => {
  const [recurringTasks, setRecurringTasks] = useState<RecurringTask[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialParams?.page || 1);
  const [pageSize] = useState(initialParams?.page_size || 20);
  const [totalPages, setTotalPages] = useState(0);

  const [frequency, setFrequency] = useState<RecurrenceFrequency | ''>(
    initialParams?.frequency || ''
  );
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'paused' | 'stopped'>('all');
  const [search, setSearch] = useState(initialParams?.search || '');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecurringTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: RecurringTaskFilterParams = {
        page,
        page_size: pageSize,
      };

      if (frequency) {
        params.frequency = frequency;
      }
      if (search.trim()) {
        params.search = search.trim();
      }

      if (statusFilter === 'active') {
        params.is_active = true;
        params.is_stopped = false;
      } else if (statusFilter === 'paused') {
        params.is_active = false;
        params.is_stopped = false;
      } else if (statusFilter === 'stopped') {
        params.is_stopped = true;
      }

      const res = await recurringTasksApi.list(params);
      setRecurringTasks(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(msg || 'Failed to load recurring tasks.');
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, frequency, statusFilter, search]);

  useEffect(() => {
    fetchRecurringTasks();
  }, [fetchRecurringTasks]);

  const createRecurringTask = async (payload: RecurringTaskCreatePayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const created = await recurringTasksApi.create(payload);
      await fetchRecurringTasks();
      return created;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to create recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const updateRecurringTask = async (id: string, payload: RecurringTaskUpdatePayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const updated = await recurringTasksApi.update(id, payload);
      await fetchRecurringTasks();
      return updated;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to update recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteRecurringTask = async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await recurringTasksApi.delete(id);
      await fetchRecurringTasks();
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to delete recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const pauseRecurringTask = async (id: string) => {
    try {
      const updated = await recurringTasksApi.pause(id);
      await fetchRecurringTasks();
      return updated;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to pause recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const resumeRecurringTask = async (id: string) => {
    try {
      const updated = await recurringTasksApi.resume(id);
      await fetchRecurringTasks();
      return updated;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to resume recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const stopRecurringTask = async (id: string) => {
    try {
      const updated = await recurringTasksApi.stop(id);
      await fetchRecurringTasks();
      return updated;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to stop recurring task.';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const skipOccurrence = async (id: string, payload: RecurringTaskSkipPayload) => {
    try {
      const updated = await recurringTasksApi.skipOccurrence(id, payload);
      await fetchRecurringTasks();
      return updated;
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      const errorMsg = msg || 'Failed to skip occurrence.';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  return {
    recurringTasks,
    total,
    page,
    pageSize,
    totalPages,
    frequency,
    setFrequency,
    statusFilter,
    setStatusFilter,
    search,
    setSearch,
    isLoading,
    error,
    setPage,
    fetchRecurringTasks,
    createRecurringTask,
    updateRecurringTask,
    deleteRecurringTask,
    pauseRecurringTask,
    resumeRecurringTask,
    stopRecurringTask,
    skipOccurrence,
  };
};

