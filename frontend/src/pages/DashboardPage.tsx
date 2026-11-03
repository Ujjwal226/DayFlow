import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { tasksApi } from '../api/tasks';
import { Task, TaskStatistics } from '../types/task';
import { TaskPriorityBadge } from '../components/tasks/TaskPriorityBadge';
import { TaskStatusBadge } from '../components/tasks/TaskStatusBadge';
import { Link } from 'react-router-dom';
import {
  User as UserIcon,
  Mail,
  ShieldCheck,
  ShieldAlert,
  LogOut,
  Layers,
  Sparkles,
  CheckSquare,
  ArrowRight,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, logout, logoutAll, resendVerification, isLoading } = useAuth();
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [isResending, setIsResending] = useState<boolean>(false);

  const [stats, setStats] = useState<TaskStatistics | null>(null);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [statsData, listData] = await Promise.all([
          tasksApi.getStatistics(),
          tasksApi.listTasks({ page: 1, page_size: 5, sort_by: 'updated_at', sort_order: 'desc' }),
        ]);
        setStats(statsData);
        setRecentTasks(listData.items);
      } catch {
        // Silently tolerate if statistics/tasks load fails
      } finally {
        setTasksLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  const handleResend = async () => {
    if (!user?.email) return;
    setIsResending(true);
    setResendStatus(null);
    try {
      const msg = await resendVerification(user.email);
      setResendStatus(msg);
    } catch {
      setResendStatus('Failed to send verification link.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
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
                to="/tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from this device"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>

            <button
              onClick={() => logoutAll()}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from all active devices and sessions"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Sign Out All</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-6 py-12 flex-1 w-full flex flex-col justify-center">
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Authenticated Session Active
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.display_name || 'Member'}!
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Your DayFlow personal productivity and financial command center.
          </p>
        </div>

        {/* Unverified Email Warning Banner */}
        {user && !user.is_verified && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-sm text-white">Your email address is unverified</div>
                <div className="text-xs text-amber-300/80 mt-0.5">
                  Verify your email to secure your account and access full communication features.
                </div>
                {resendStatus && (
                  <div className="text-xs text-emerald-400 font-medium mt-1">{resendStatus}</div>
                )}
              </div>
            </div>
            <button
              onClick={handleResend}
              disabled={isResending}
              className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 text-xs font-medium transition shrink-0 disabled:opacity-50"
            >
              {isResending ? 'Sending...' : 'Resend Verification Email'}
            </button>
          </div>
        )}

        {/* Profile Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur shadow-2xl space-y-6">
          <div className="flex items-center justify-between pb-6 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <UserIcon className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">{user?.display_name}</h2>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Mail className="w-3 h-3" />
                  <span>{user?.email}</span>
                </div>
              </div>
            </div>

            <div>
              {user?.is_verified ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Unverified Account
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-slate-400 mb-1">User Identifier (UUID)</div>
              <div className="font-mono text-slate-200 select-all truncate">{user?.id}</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div className="text-slate-400 mb-1">Account Created</div>
              <div className="text-slate-200">
                {user?.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/60 flex items-center gap-2 text-xs text-slate-400">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>
              Session secured with memory-only JWT access tokens and HttpOnly rotating refresh cookies.
            </span>
          </div>
        </div>

        {/* Task Management Overview Section */}
        <div className="mt-8 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur shadow-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <CheckSquare className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Tasks Overview</h2>
                <p className="text-xs text-slate-400">Quick snapshot of your action items</p>
              </div>
            </div>

            <Link
              to="/tasks"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition"
            >
              <span>Manage Tasks</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">Active Tasks</span>
              <span className="text-xl font-bold text-white">{stats ? stats.total : 0}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">Completed</span>
              <span className="text-xl font-bold text-emerald-400">{stats ? stats.completed : 0}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">Overdue</span>
              <span className="text-xl font-bold text-rose-400">{stats ? stats.overdue : 0}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">Upcoming</span>
              <span className="text-xl font-bold text-amber-400">{stats ? stats.upcoming : 0}</span>
            </div>
          </div>

          {/* Recent Tasks List */}
          <div className="mt-6">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Recently Updated Tasks
            </h3>
            {tasksLoading ? (
              <div className="py-6 text-center text-xs text-slate-500">Loading tasks...</div>
            ) : recentTasks.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                No tasks yet. Create your first task to get started.
              </div>
            ) : (
              <div className="space-y-2">
                {recentTasks.map((t) => (
                  <Link
                    key={t.id}
                    to={`/tasks/${t.id}`}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-950 transition group"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-3">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${
                        t.status === 'COMPLETED' ? 'bg-emerald-500' : t.is_overdue ? 'bg-rose-500' : 'bg-slate-500'
                      }`} />
                      <span className={`text-xs text-slate-200 group-hover:text-emerald-400 transition truncate ${
                        t.status === 'COMPLETED' ? 'line-through text-slate-500' : ''
                      }`}>
                        {t.title}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <TaskStatusBadge status={t.status} />
                      <TaskPriorityBadge priority={t.priority} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600">
        DayFlow &copy; 2026. Production Authentication Foundation.
      </footer>
    </div>
  );
};

