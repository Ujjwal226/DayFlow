export interface RootResponse {
  app_name: string;
  version: string;
  status: string;
  documentation: string;
}

export interface LivenessResponse {
  status: string;
  timestamp: string;
  service: string;
}

export interface ReadinessResponse {
  status: string;
  timestamp: string;
  service: string;
  database: 'connected' | 'disconnected' | string;
  details?: string;
}

export interface SystemHealthState {
  liveness: LivenessResponse | null;
  readiness: ReadinessResponse | null;
  root: RootResponse | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: Date | null;
}

