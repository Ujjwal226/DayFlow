import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useActivityLogs } from '../hooks/useActivityLogs';
import { ActivityFilters } from '../components/activity/ActivityFilters';
import { ActivityFeed } from '../components/activity/ActivityFeed';
import {
  History,
  LayoutDashboard,
  CheckSquare,
  FolderKanban,
  Repeat,
  LogOut,
  RefreshCw,
} from 'lucide-react';

export const ActivityPage: React.FC = () => {
  const { logout } = useAuth();
  const {
    logs,
    total,
    page,
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
    fetchActivities,
    resetFilters,
  } = useActivityLogs();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/40 backdrop-blur sticky top-0 z-40">
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
                <LayoutDashboard className="w-3.5 h-3.5" />
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
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <History className="w-3.5 h-3.5" />
                <span>Activity</span>
              </Link>
              <Link
                to="/analytics"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
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
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <History className="w-6 h-6 text-emerald-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Activity Feed
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Audit trail and chronological history of actions across your workspace ({total} total).
            </p>
          </div>

          <button
            onClick={() => fetchActivities()}
            className="self-start sm:self-auto px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filters */}
        <ActivityFilters
          actionFilter={actionFilter}
          setActionFilter={setActionFilter}
          entityFilter={entityFilter}
          setEntityFilter={setEntityFilter}
          startDate={startDate}
          setStartDate={setStartDate}
          endDate={endDate}
          setEndDate={setEndDate}
          onReset={resetFilters}
        />

        {/* Feed List */}
        <ActivityFeed
          logs={logs}
          isLoading={isLoading}
          error={error}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      </main>
    </div>
  );
};

