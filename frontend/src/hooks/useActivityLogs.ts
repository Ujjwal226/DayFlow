import { useState, useEffect, useCallback } from 'react';
import { activityLogsApi } from '../api/activityLogs';
import {
  ActivityLog,
  ActivityLogQueryParams,
} from '../types/activityLog';

export const useActivityLogs = (initialParams: ActivityLogQueryParams = {}) => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(initialParams.page || 1);
  const [pageSize, setPageSize] = useState<number>(initialParams.page_size || 20);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [actionFilter, setActionFilter] = useState<string>(initialParams.action || '');
  const [entityFilter, setEntityFilter] = useState<string>(initialParams.entity_type || '');
  const [startDate, setStartDate] = useState<string>(initialParams.start_date || '');
  const [endDate, setEndDate] = useState<string>(initialParams.end_date || '');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await activityLogsApi.getGlobalActivities({
        action: actionFilter || undefined,
        entity_type: entityFilter || undefined,
        start_date: startDate ? new Date(startDate).toISOString() : undefined,
        end_date: endDate ? new Date(endDate).toISOString() : undefined,
        page,
        page_size: pageSize,
      });
      setLogs(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load activity logs.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [actionFilter, entityFilter, startDate, endDate, page, pageSize]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  const resetFilters = () => {
    setActionFilter('');
    setEntityFilter('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  return {
    logs,
    total,
    page,
    pageSize,
    totalPages,
    actionFilter,
    setActionFilter,
    entityFilter,
    setEntityFilter,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    isLoading,
    error,
    setPage,
    setPageSize,
    fetchActivities,
    resetFilters,
  };
};

