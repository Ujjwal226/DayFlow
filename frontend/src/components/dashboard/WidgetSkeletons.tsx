import React from 'react';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', style }) => (
  <div style={style} className={`animate-pulse bg-slate-800/70 rounded-lg ${className}`} />
);

export const TaskListSkeleton: React.FC = () => (
  <div className="space-y-2 py-1">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 animate-pulse"
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-3">
          <Skeleton className="w-2.5 h-2.5 rounded-full shrink-0" />
          <div className="flex-1 space-y-1">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-2 w-1/3" />
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Skeleton className="h-4 w-12 rounded-full" />
          <Skeleton className="h-4 w-12 rounded-full" />
        </div>
      </div>
    ))}
  </div>
);

export const KpiGridSkeleton: React.FC = () => (
  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-1">
    {[1, 2, 3, 4].map((i) => (
      <div
        key={i}
        className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 animate-pulse space-y-2"
      >
        <div className="flex justify-between items-center">
          <Skeleton className="h-2.5 w-16" />
          <Skeleton className="h-3.5 w-3.5 rounded-full" />
        </div>
        <Skeleton className="h-6 w-12" />
        <Skeleton className="h-2 w-20" />
      </div>
    ))}
  </div>
);

export const ActivityFeedSkeleton: React.FC = () => (
  <div className="space-y-2 py-1">
    {[1, 2, 3, 4].map((i) => (
      <div
        key={i}
        className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 animate-pulse"
      >
        <Skeleton className="w-7 h-7 rounded-lg shrink-0" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-2 w-1/4" />
        </div>
      </div>
    ))}
  </div>
);

export const ProjectOverviewSkeleton: React.FC = () => (
  <div className="space-y-3 py-1">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 animate-pulse space-y-2"
      >
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 flex-1">
            <Skeleton className="w-2.5 h-2.5 rounded-full" />
            <Skeleton className="h-3.5 w-1/2" />
          </div>
          <Skeleton className="h-3 w-8" />
        </div>
        <Skeleton className="h-1.5 w-full rounded-full" />
        <div className="flex justify-between">
          <Skeleton className="h-2 w-16" />
          <Skeleton className="h-2 w-12" />
        </div>
      </div>
    ))}
  </div>
);

export const TrendChartSkeleton: React.FC = () => (
  <div className="space-y-4 py-1 animate-pulse">
    <div className="flex items-end justify-between gap-2 h-28 pt-4 px-2">
      {[40, 70, 30, 90, 50, 80, 60].map((h, idx) => (
        <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
          <Skeleton className="h-2 w-4" />
          <div className="w-full max-w-[28px] bg-slate-800/50 rounded-t-md flex items-end h-20">
            <Skeleton
              className="w-full rounded-t-md"
              style={{ height: `${h}%` }}
            />
          </div>
          <Skeleton className="h-2.5 w-3" />
        </div>
      ))}
    </div>
    <div className="flex justify-between pt-2 border-t border-slate-800/80">
      <Skeleton className="h-2.5 w-32" />
      <Skeleton className="h-2.5 w-16" />
    </div>
  </div>
);
