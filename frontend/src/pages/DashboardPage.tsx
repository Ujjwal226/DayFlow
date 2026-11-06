import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { dashboardApi } from '../api/dashboard';
import { DashboardWidgetConfig } from '../types/dashboard';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { DashboardCustomizerModal } from '../components/dashboard/DashboardCustomizerModal';
import {
  Layers,
  CheckSquare,
  Calendar,
  LogOut,
  ShieldAlert,
  Sliders,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { logout, logoutAll, isLoading: authLoading } = useAuth();

  const [widgets, setWidgets] = useState<DashboardWidgetConfig[]>([]);
  const [layoutLoading, setLayoutLoading] = useState<boolean>(true);
  const [layoutError, setLayoutError] = useState<string | null>(null);

  const [isCustomizerOpen, setIsCustomizerOpen] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const customizeBtnRef = React.useRef<HTMLButtonElement>(null);

  const fetchLayout = async () => {
    setLayoutLoading(true);
    setLayoutError(null);
    try {
      const data = await dashboardApi.getLayout();
      setWidgets(data.widgets);
    } catch {
      setLayoutError('Failed to load your dashboard configuration.');
    } finally {
      setLayoutLoading(false);
    }
  };

  useEffect(() => {
    fetchLayout();
  }, []);

  const handleCloseCustomizer = () => {
    setIsCustomizerOpen(false);
    setSaveError(null);
    setTimeout(() => {
      customizeBtnRef.current?.focus();
    }, 50);
  };

  const handleSaveLayout = async (updatedWidgets: DashboardWidgetConfig[]) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const saved = await dashboardApi.updateLayout(updatedWidgets);
      setWidgets(saved.widgets);
      setIsCustomizerOpen(false);
      setTimeout(() => {
        customizeBtnRef.current?.focus();
      }, 50);
    } catch {
      setSaveError('Failed to save layout changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetLayout = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const defaultLayout = await dashboardApi.resetLayout();
      setWidgets(defaultLayout.widgets);
      setIsCustomizerOpen(false);
      setTimeout(() => {
        customizeBtnRef.current?.focus();
      }, 50);
    } catch {
      setSaveError('Failed to reset layout to defaults.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
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
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/calendar"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Calendar</span>
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
                <span>Projects</span>
              </Link>
              <Link
                to="/recurring-tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Recurring</span>
              </Link>
              <Link
                to="/activity"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
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
              disabled={authLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from this device"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>

            <button
              onClick={() => logoutAll()}
              disabled={authLoading}
              className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from all active devices and sessions"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out All</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-10 flex-1 w-full flex flex-col">
        {/* Workspace Action Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Personal Workspace
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1">
              Your customized productivity dashboard and actionable overview.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              ref={customizeBtnRef}
              onClick={() => setIsCustomizerOpen(true)}
              className="px-4 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-emerald-400 border border-emerald-500/20 hover:border-emerald-500/40 text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-emerald-500/5 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              <Sliders className="w-4 h-4" />
              <span>Customize Dashboard</span>
            </button>
          </div>
        </div>

        {/* Dashboard Grid / Loading / Error State */}
        {layoutLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
            <RefreshCw className="w-7 h-7 animate-spin text-emerald-400" />
            <p className="text-sm font-medium">Loading your dashboard layout...</p>
          </div>
        ) : layoutError ? (
          <div className="flex-1 flex flex-col items-center justify-center py-16 text-center max-w-md mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-4">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h2 className="text-base font-bold text-white mb-1">Layout Unavailable</h2>
            <p className="text-xs text-slate-400 mb-4">{layoutError}</p>
            <button
              onClick={fetchLayout}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-emerald-500/20"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry Loading</span>
            </button>
          </div>
        ) : (
          <DashboardGrid widgets={widgets} />
        )}

        {/* Customizer Modal */}
        <DashboardCustomizerModal
          isOpen={isCustomizerOpen}
          onClose={handleCloseCustomizer}
          currentWidgets={widgets}
          onSave={handleSaveLayout}
          onReset={handleResetLayout}
          isSaving={isSaving}
          saveError={saveError}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600">
        DayFlow &copy; 2026. Production Authentication Foundation.
      </footer>
    </div>
  );
};
