import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { WidgetSize } from '../../types/dashboard';

interface WidgetContainerProps {
  title: string;
  description?: string;
  size?: WidgetSize;
  isLoading?: boolean;
  skeleton?: React.ReactNode;
  error?: string | null;
  onRetry?: () => void;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const WidgetContainer: React.FC<WidgetContainerProps> = ({
  title,
  description,
  isLoading = false,
  skeleton,
  error = null,
  onRetry,
  headerAction,
  children,
  className = '',
}) => {
  return (
    <div
      className={`h-full flex flex-col bg-slate-900/80 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur shadow-xl transition-all duration-200 hover:border-slate-700/80 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3.5 mb-4 border-b border-slate-800/80 gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="text-sm sm:text-base font-bold text-white tracking-tight truncate">
            {title}
          </h2>
          {description && (
            <p className="text-xs text-slate-400 mt-0.5 truncate">{description}</p>
          )}
        </div>
        {headerAction && <div className="shrink-0">{headerAction}</div>}
      </div>

      {/* Body Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {isLoading ? (
          skeleton ? (
            skeleton
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center py-8 text-slate-400 space-y-2">
              <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
              <span className="text-xs">Loading widget data...</span>
            </div>
          )
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center py-6 text-center px-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <AlertCircle className="w-6 h-6 text-rose-400 mb-2" />
            <p className="text-xs text-rose-200 font-medium mb-1">Failed to load content</p>
            <p className="text-xs text-rose-300/70 max-w-xs mb-3">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/30 text-xs font-medium transition flex items-center gap-1.5"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            )}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
};

