import React from 'react';
import { useHealthCheck } from '../hooks/useHealthCheck';
import {
  Activity,
  Database,
  Server,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  ArrowUpRight,
} from 'lucide-react';

export const WelcomePage: React.FC = () => {
  const { root, liveness, readiness, isLoading, error, lastChecked, refetch } =
    useHealthCheck(15000);

  const isBackendHealthy = liveness?.status === 'ok';
  const isDbHealthy = readiness?.database === 'connected';

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
              DF
            </div>
            <span className="font-semibold text-lg tracking-tight text-white">
              DayFlow
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60 font-mono">
              Part 1A: Foundation
            </span>
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Refresh Health Status"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`}
              />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-12 flex-1 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Clean Architecture Foundation Ready
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-6">
            DayFlow
          </h1>
          <p className="text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
            A production-quality, multi-user personal productivity and finance
            management platform. Engineered for speed, data sovereignty, and reliable daily planning.
          </p>
        </div>

        {/* System Health Status Panel */}
        <div className="max-w-3xl mx-auto w-full bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 sm:p-8 backdrop-blur shadow-2xl">
          <div className="flex items-center justify-between pb-6 border-b border-slate-700/60 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-slate-700/50 text-emerald-400">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">
                  System Health & Connectivity
                </h2>
                <p className="text-xs text-slate-400">
                  Live verification of backend services and PostgreSQL database
                </p>
              </div>
            </div>

            {lastChecked && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <Clock className="w-3.5 h-3.5" />
                <span>{lastChecked.toLocaleTimeString()}</span>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
              <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="font-semibold text-rose-300">Backend Connection Error</div>
                <div className="text-rose-400/90 text-xs mt-1">{error}</div>
              </div>
            </div>
          )}

          {/* Health Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Backend API Root & Meta */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/50 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <Server className="w-4 h-4 text-slate-400" />
                  <span>Backend Core</span>
                </div>
                {root ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )}
              </div>
              <div>
                <div className="text-xl font-bold text-white">
                  {root ? root.app_name : 'DayFlow Core'}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Version: <span className="font-mono text-slate-300">{root?.version || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Application Liveness */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/50 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <Activity className="w-4 h-4 text-slate-400" />
                  <span>API Liveness</span>
                </div>
                {isBackendHealthy ? (
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"></span>
                ) : (
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.6)]"></span>
                )}
              </div>
              <div>
                <div className="text-xl font-bold capitalize text-white">
                  {liveness ? liveness.status : isLoading ? 'Checking...' : 'Offline'}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Service:{' '}
                  <span className="font-mono text-slate-300">
                    {liveness?.service || 'backend'}
                  </span>
                </div>
              </div>
            </div>

            {/* Database Readiness */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/50 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <Database className="w-4 h-4 text-slate-400" />
                  <span>PostgreSQL</span>
                </div>
                {isDbHealthy ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-amber-400" />
                )}
              </div>
              <div>
                <div className="text-xl font-bold capitalize text-white">
                  {readiness?.database || (isLoading ? 'Checking...' : 'Disconnected')}
                </div>
                <div className="text-xs text-slate-400 mt-1 truncate" title={readiness?.details || ''}>
                  {readiness?.details || 'Database connection status'}
                </div>
              </div>
            </div>
          </div>

          {/* Quick links & Documentation */}
          <div className="mt-6 pt-5 border-t border-slate-700/60 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-slate-400" />
              <span>FastAPI 0.115 • React 18 • TypeScript • Tailwind CSS • SQLAlchemy 2.0</span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 font-medium transition"
            >
              <span>Swagger API Docs</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        DayFlow &copy; 2026. Production-Ready Architecture & Foundation.
      </footer>
    </div>
  );
};

