import React, { useState, useEffect } from 'react';
import {
  Settings,
  Sun,
  Moon,
  Server,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sliders,
  ShieldCheck,
  User as UserIcon,
  LogOut,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { healthApi } from '../lib/api';
import type { HealthResponse } from '../types/api';
import { toast } from 'sonner';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  const checkBackendHealth = async () => {
    setCheckingHealth(true);
    setHealthError(null);
    try {
      const data = await healthApi.check();
      setHealth(data);
      toast.success('Connected to DayFlow backend');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend unreachable';
      setHealthError(msg);
      toast.error('Backend connection failed: ' + msg);
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-4xl">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 text-violet-500 font-medium text-xs tracking-wider uppercase mb-1">
          <Settings className="w-4 h-4" />
          <span>Preferences & Diagnostics</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
          Settings
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Customize your DayFlow experience and inspect your backend connectivity.
        </p>
      </div>

      {/* Theme Preference Section */}
      <div className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center shrink-0">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">Appearance</h2>
            <p className="text-xs text-[var(--text-secondary)]">
              Choose your preferred visual theme. Persisted locally on this device.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {/* Dark Mode option */}
          <button
            type="button"
            onClick={() => setTheme('dark')}
            className={`flex items-center justify-between p-4 rounded-xl border text-left transition-all ${
              theme === 'dark'
                ? 'border-violet-500 bg-violet-500/10 text-[var(--text-primary)] shadow-sm'
                : 'border-[var(--bg-border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:border-violet-500/30'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-[var(--bg-surface)] text-amber-400">
                <Sun className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">Dark Theme</p>
                <p className="text-xs text-[var(--text-secondary)]">Charcoal & purple surfaces</p>
              </div>
            </div>
            {theme === 'dark' && (
              <span className="w-2.5 h-2.5 rounded-full bg-violet-500" />
            )}
          </button>

          {/* Light Mode option */}
          <button
            type="button"
            onClick={() => setTheme('light')}
            className={`flex items-center justify-between p-4 rounded-xl border text-left transition-all ${
              theme === 'light'
                ? 'border-violet-500 bg-violet-500/10 text-[var(--text-primary)] shadow-sm'
                : 'border-[var(--bg-border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:border-violet-500/30'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-[var(--bg-surface)] text-indigo-500">
                <Moon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">Light Theme</p>
                <p className="text-xs text-[var(--text-secondary)]">Clean, luminous surfaces</p>
              </div>
            </div>
            {theme === 'light' && (
              <span className="w-2.5 h-2.5 rounded-full bg-violet-500" />
            )}
          </button>
        </div>
      </div>

      {/* Backend API Connection & Diagnostics */}
      <div className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center shrink-0">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-[var(--text-primary)]">Backend API Status</h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Live connection check to FastAPI and SQLite engine.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={checkBackendHealth}
            disabled={checkingHealth}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-[var(--bg-border)] text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checkingHealth ? 'animate-spin' : ''}`} />
            <span>Test Connection</span>
          </button>
        </div>

        <div className="p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--text-secondary)]">API Base URL:</span>
            <code className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--bg-surface)] text-violet-400">
              {apiBaseUrl}
            </code>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--text-secondary)]">Server Status:</span>
            {checkingHealth ? (
              <span className="text-xs text-[var(--text-secondary)]">Pinging /health...</span>
            ) : health ? (
              <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {health.status.toUpperCase()} (v{health.version})
              </span>
            ) : (
              <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-500 border border-rose-500/20">
                <AlertCircle className="w-3.5 h-3.5 mr-1" />
                Disconnected
              </span>
            )}
          </div>

          {healthError && (
            <p className="text-xs text-rose-500 pt-1 border-t border-[var(--bg-border)]">
              {healthError}
            </p>
          )}
        </div>
      </div>

      {/* Account & Authentication Section (Stage 5) */}
      <div className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center shrink-0">
            <UserIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">Account & Authentication</h2>
            <p className="text-xs text-[var(--text-secondary)]">
              Manage your personal credentials and session security.
            </p>
          </div>
        </div>

        {user ? (
          <div className="p-4 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md">
                {user.full_name
                  ? user.full_name.charAt(0).toUpperCase()
                  : user.email.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-bold text-[var(--text-primary)]">
                  {user.full_name || 'Personal Account'}
                </p>
                <p className="text-xs text-[var(--text-secondary)]">{user.email}</p>
                <span className="inline-flex items-center px-2 py-0.5 mt-1 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                  Authenticated User #{user.id}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={logout}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 transition-colors flex items-center justify-center space-x-2 shrink-0"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        ) : (
          <p className="text-xs text-[var(--text-muted)]">No active user session.</p>
        )}

        <div className="flex items-center space-x-2 text-xs text-[var(--text-muted)] pt-1">
          <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
          <span>All tasks, calendar events, analytics, and history are private to your user ID.</span>
        </div>
      </div>

      {/* System Info */}
      <div className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--bg-border)] shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-500 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">About DayFlow</h2>
            <p className="text-xs text-[var(--text-secondary)]">
              Personal task management application built with FastAPI and React.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
          <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)]">
            <span className="text-[var(--text-secondary)] block">Stage</span>
            <span className="font-semibold text-[var(--text-primary)] text-sm mt-0.5 block">Stage 5: Multi-User</span>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)]">
            <span className="text-[var(--text-secondary)] block">Frontend</span>
            <span className="font-semibold text-[var(--text-primary)] text-sm mt-0.5 block">React + Vite + TS</span>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)]">
            <span className="text-[var(--text-secondary)] block">Styling</span>
            <span className="font-semibold text-[var(--text-primary)] text-sm mt-0.5 block">Tailwind CSS v4</span>
          </div>
          <div className="p-3 rounded-xl bg-[var(--bg-elevated)] border border-[var(--bg-border)]">
            <span className="text-[var(--text-secondary)] block">Backend</span>
            <span className="font-semibold text-[var(--text-primary)] text-sm mt-0.5 block">FastAPI + Supabase / PostgreSQL</span>
          </div>
        </div>
      </div>
    </div>
  );
};
