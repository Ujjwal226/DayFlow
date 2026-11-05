import React from 'react';
import { Tag, CheckCircle2, Clock } from 'lucide-react';
import { CategoryAnalyticsResponse } from '../../types/analytics';

interface CategoryBreakdownSectionProps {
  categoriesData: CategoryAnalyticsResponse | null;
  loading: boolean;
}

export const CategoryBreakdownSection: React.FC<CategoryBreakdownSectionProps> = ({
  categoriesData,
  loading,
}) => {
  if (loading && !categoriesData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-56 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading category breakdown...</span>
      </div>
    );
  }

  const categories = categoriesData?.categories || [];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Tag className="w-4 h-4 text-teal-400" />
            <span>Category Breakdown</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
              {categories.length} {categories.length === 1 ? 'category' : 'categories'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Distribution of tasks and completion rates by category (including Uncategorized).
          </p>
        </div>
      </div>

      {categories.length === 0 ? (
        <div className="p-8 rounded-xl border border-dashed border-slate-800 text-center space-y-1">
          <p className="text-sm font-medium text-slate-400">No categories found</p>
          <p className="text-xs text-slate-500">
            Tasks will automatically group into categories or the Uncategorized bucket.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {categories.map((cat, idx) => {
            const isUncategorized = cat.category_id === null;
            return (
              <div
                key={cat.category_id || `uncat-${idx}`}
                className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/70 hover:border-slate-700/80 transition space-y-2"
              >
                <div className="flex items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{
                        backgroundColor: cat.category_color || (isUncategorized ? '#64748b' : '#14b8a6'),
                      }}
                    />
                    <span className="font-semibold text-white truncate">
                      {cat.category_name}
                    </span>
                    {isUncategorized && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-slate-300 shrink-0">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>{cat.completed_tasks}</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-amber-400" />
                      <span>{cat.pending_tasks}</span>
                    </span>
                    <span className="text-slate-400">
                      Total: <strong className="text-white">{cat.total_tasks}</strong>
                    </span>
                    <span className="font-semibold text-teal-400 w-12 text-right">
                      {cat.completion_rate}%
                    </span>
                  </div>
                </div>

                {/* Compact distribution progress bar */}
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400 transition-all duration-300"
                    style={{ width: `${Math.min(cat.completion_rate, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

