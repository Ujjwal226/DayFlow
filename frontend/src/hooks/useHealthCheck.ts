import { useState, useEffect, useCallback } from 'react';
import { healthApi } from '../api/health';
import { SystemHealthState } from '../types/api';

export function useHealthCheck(pollIntervalMs?: number) {
  const [state, setState] = useState<SystemHealthState>({
    liveness: null,
    readiness: null,
    root: null,
    isLoading: true,
    error: null,
    lastChecked: null,
  });

  const checkHealth = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const [rootData, liveData, readyData] = await Promise.all([
        healthApi.getRoot(),
        healthApi.getLiveness(),
        healthApi.getReadiness().catch((err) => {
          // If 503 is returned, readiness may still contain response data or error
          return {
            status: 'unhealthy',
            service: 'backend',
            database: 'disconnected',
            timestamp: new Date().toISOString(),
            details: err.message || 'Database unavailable',
          };
        }),
      ]);

      setState({
        root: rootData,
        liveness: liveData,
        readiness: readyData,
        isLoading: false,
        error: null,
        lastChecked: new Date(),
      });
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Backend unreachable';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMsg,
        lastChecked: new Date(),
      }));
    }
  }, []);

  useEffect(() => {
    checkHealth();

    if (pollIntervalMs && pollIntervalMs > 0) {
      const timer = setInterval(checkHealth, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [checkHealth, pollIntervalMs]);

  return { ...state, refetch: checkHealth };
}

