import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  CheckSquare,
  FolderKanban,
  Repeat,
  History,
  Layers,
  LogOut,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { analyticsApi } from '../api/analytics';
import {
  ProductivityOverviewResponse,
  ProductivityTrendsResponse,
  ConsistencyAnalyticsResponse,
  ProjectAnalyticsResponse,
  CategoryAnalyticsResponse,
  WorkloadAnalyticsResponse,
  RecurringAnalyticsResponse,
} from '../types/analytics';
import { AnalyticsOverviewCards } from '../components/analytics/AnalyticsOverviewCards';
import { CompletionTrendChart } from '../components/analytics/CompletionTrendChart';
import { ProductivityHeatmap } from '../components/analytics/ProductivityHeatmap';
import { ProjectPerformanceSection } from '../components/analytics/ProjectPerformanceSection';
import { CategoryBreakdownSection } from '../components/analytics/CategoryBreakdownSection';
import { WorkloadSection } from '../components/analytics/WorkloadSection';
import { RecurringInsightsSection } from '../components/analytics/RecurringInsightsSection';
import {
  AnalyticsDateFilter,
  DateRangePreset,
  AggregationInterval,
} from '../components/analytics/AnalyticsDateFilter';

export const AnalyticsPage: React.FC = () => {
  const { logout } = useAuth();

  // Filters state
  const [preset, setPreset] = useState<DateRangePreset>('30d');
  const [interval, setInterval] = useState<AggregationInterval>('daily');
  const [timezone, setTimezone] = useState<string>('Asia/Kolkata');
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');

  // Analytics datasets
  const [overview, setOverview] = useState<ProductivityOverviewResponse | null>(null);
  const [trends, setTrends] = useState<ProductivityTrendsResponse | null>(null);
  const [consistency, setConsistency] = useState<ConsistencyAnalyticsResponse | null>(null);
  const [projectsData, setProjectsData] = useState<ProjectAnalyticsResponse | null>(null);
  const [categoriesData, setCategoriesData] = useState<CategoryAnalyticsResponse | null>(null);
  const [workloadData, setWorkloadData] = useState<WorkloadAnalyticsResponse | null>(null);
  const [recurringData, setRecurringData] = useState<RecurringAnalyticsResponse | null>(null);

  // Loading and error states
  const [loading, setLoading] = useState<boolean>(true);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Race condition guard: track latest request id
  const requestIdRef = useRef<number>(0);

  // Helper to derive query params based on preset
  const getFilterParams = useCallback(() => {
    let days: number | undefined;
    let start_date: string | undefined;
    let end_date: string | undefined;

    if (preset === '7d') days = 7;
    else if (preset === '30d') days = 30;
    else if (preset === '90d') days = 90;
    else if (preset === 'custom') {
      if (customStartDate) start_date = customStartDate;
      if (customEndDate) end_date = customEndDate;
    }

    return { days, start_date, end_date };
  }, [preset, customStartDate, customEndDate]);

  // Fetch all endpoints concurrently without full-page cascade failures
  const fetchAllAnalytics = useCallback(async () => {
    const currentReqId = ++requestIdRef.current;
    setLoading(true);
    const newErrors: Record<string, string> = {};
    const { days, start_date, end_date } = getFilterParams();

    // 1. Overview
    const pOverview = analyticsApi
      .getOverview({ days, start_date, end_date })
      .then((data) => {
        if (currentReqId === requestIdRef.current) setOverview(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.overview = err?.response?.data?.detail || 'Failed to load overview KPIs.';
        }
      });

    // 2. Trends
    const pTrends = analyticsApi
      .getTrends({
        interval,
        days,
        start_date,
        end_date,
        timezone,
      })
      .then((data) => {
        if (currentReqId === requestIdRef.current) setTrends(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.trends = err?.response?.data?.detail || 'Failed to load trends data.';
        }
      });

    // 3. Consistency
    const pConsistency = analyticsApi
      .getConsistency(timezone)
      .then((data) => {
        if (currentReqId === requestIdRef.current) setConsistency(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.consistency =
            err?.response?.data?.detail || 'Failed to load consistency streaks.';
        }
      });

    // 4. Projects
    const pProjects = analyticsApi
      .getProjects()
      .then((data) => {
        if (currentReqId === requestIdRef.current) setProjectsData(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.projects =
            err?.response?.data?.detail || 'Failed to load project analytics.';
        }
      });

    // 5. Categories
    const pCategories = analyticsApi
      .getCategories()
      .then((data) => {
        if (currentReqId === requestIdRef.current) setCategoriesData(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.categories =
            err?.response?.data?.detail || 'Failed to load category analytics.';
        }
      });

    // 6. Workload
    const pWorkload = analyticsApi
      .getWorkload(timezone)
      .then((data) => {
        if (currentReqId === requestIdRef.current) setWorkloadData(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.workload =
            err?.response?.data?.detail || 'Failed to load workload distribution.';
        }
      });

    // 7. Recurring
    const pRecurring = analyticsApi
      .getRecurring(timezone)
      .then((data) => {
        if (currentReqId === requestIdRef.current) setRecurringData(data);
      })
      .catch((err) => {
        if (currentReqId === requestIdRef.current) {
          newErrors.recurring =
            err?.response?.data?.detail || 'Failed to load recurring task adherence.';
        }
      });

    await Promise.allSettled([
      pOverview,
      pTrends,
      pConsistency,
      pProjects,
      pCategories,
      pWorkload,
      pRecurring,
    ]);

    if (currentReqId === requestIdRef.current) {
      setErrors(newErrors);
      setLoading(false);
    }
  }, [getFilterParams, interval, timezone]);

  useEffect(() => {
    fetchAllAnalytics();
  }, [fetchAllAnalytics]);

  const hasAnyErrors = Object.keys(errors).length > 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
                DF
              </div>
              <span className="font-semibold text-lg tracking-tight text-white">
                DayFlow
              </span>
            </Link>

            <nav className="hidden sm:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
              <Link
                to="/projects"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <FolderKanban className="w-3.5 h-3.5" />
                <span>Projects</span>
              </Link>
              <Link
                to="/recurring-tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Repeat className="w-3.5 h-3.5" />
                <span>Recurring</span>
              </Link>
              <Link
                to="/activity"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <History className="w-3.5 h-3.5" />
                <span>Activity</span>
              </Link>
              <Link
                to="/analytics"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Analytics</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Page Title & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-emerald-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Productivity Analytics & Insights
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Comprehensive task completion rates, workload distribution, habit consistency, and recurring adherence.
            </p>
          </div>
        </div>

        {/* Global Error Banner if any individual endpoint fails */}
        {hasAnyErrors && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-start justify-between gap-3 text-xs text-rose-300">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-rose-200">
                  Some analytics widgets could not be fully loaded:
                </p>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-rose-300/90">
                  {Object.entries(errors).map(([k, msg]) => (
                    <li key={k}>
                      <span className="capitalize">{k}</span>: {msg}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <button
              onClick={fetchAllAnalytics}
              className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/40 text-xs font-medium flex items-center gap-1 shrink-0"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Filters and Controls */}
        <AnalyticsDateFilter
          preset={preset}
          onPresetChange={setPreset}
          customStartDate={customStartDate}
          onCustomStartDateChange={setCustomStartDate}
          customEndDate={customEndDate}
          onCustomEndDateChange={setCustomEndDate}
          interval={interval}
          onIntervalChange={setInterval}
          timezone={timezone}
          onTimezoneChange={setTimezone}
          onRefresh={fetchAllAnalytics}
          loading={loading}
        />

        {/* Section A: Overview KPI Cards */}
        <AnalyticsOverviewCards overview={overview} loading={loading} />

        {/* Section B: Productivity Trends Chart */}
        <CompletionTrendChart trends={trends} loading={loading} />

        {/* Section C: Productivity Consistency & Streaks */}
        <ProductivityHeatmap consistency={consistency} loading={loading} />

        {/* Section D & E: Project Performance & Category Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ProjectPerformanceSection projectsData={projectsData} loading={loading} />
          <CategoryBreakdownSection categoriesData={categoriesData} loading={loading} />
        </div>

        {/* Section F: Workload & Deadline Horizons */}
        <WorkloadSection workloadData={workloadData} loading={loading} />

        {/* Section G: Recurring Task Insights */}
        <RecurringInsightsSection recurringData={recurringData} loading={loading} />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-600">
        <p>DayFlow &copy; {new Date().getFullYear()} &bull; Productivity Analytics</p>
      </footer>
    </div>
  );
};

