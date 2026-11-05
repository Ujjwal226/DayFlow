import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Info,
} from 'lucide-react';
import { ProductivityTrendsResponse, TrendBucket } from '../../types/analytics';

interface CompletionTrendChartProps {
  trends: ProductivityTrendsResponse | null;
  loading: boolean;
}

export const CompletionTrendChart: React.FC<CompletionTrendChartProps> = ({
  trends,
  loading,
}) => {
  const [hoveredBucket, setHoveredBucket] = useState<TrendBucket | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(
    null
  );

  if (loading && !trends) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-80 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading trend metrics...</span>
      </div>
    );
  }

  if (!trends) {
    return null;
  }

  const buckets = trends.buckets;
  const comparison = trends.comparison;

  // Chart dimensions & margins
  const width = 800;
  const height = 260;
  const margin = { top: 20, right: 25, bottom: 40, left: 40 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Compute min and max values across all 4 series
  // Note: net_completions can be negative!
  let minY = 0;
  let maxY = 5; // minimum top range to avoid flat divide by zero

  buckets.forEach((b) => {
    const minVal = Math.min(
      b.net_completions,
      0,
      b.created_count,
      b.gross_completions,
      b.reopened_count
    );
    const maxVal = Math.max(
      b.created_count,
      b.gross_completions,
      b.reopened_count,
      b.net_completions
    );
    if (minVal < minY) minY = minVal;
    if (maxVal > maxY) maxY = maxVal;
  });

  // Add 10% head room
  maxY = Math.ceil(maxY * 1.15) || 5;
  if (minY < 0) {
    minY = Math.floor(minY * 1.15);
  }

  const yRange = maxY - minY || 1;
  const getY = (val: number) => {
    return margin.top + innerHeight - ((val - minY) / yRange) * innerHeight;
  };

  const getX = (index: number) => {
    if (buckets.length <= 1) return margin.left + innerWidth / 2;
    return margin.left + (index / (buckets.length - 1)) * innerWidth;
  };

  const zeroY = getY(0);

  // Generate SVG paths
  const makePath = (valExtractor: (b: TrendBucket) => number) => {
    if (buckets.length === 0) return '';
    return buckets
      .map((b, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(valExtractor(b))}`)
      .join(' ');
  };

  const createdPath = makePath((b) => b.created_count);
  const grossPath = makePath((b) => b.gross_completions);
  const reopenedPath = makePath((b) => b.reopened_count);
  const netPath = makePath((b) => b.net_completions);

  // Grid tick counts
  const yTicks = [minY, Math.round(minY + yRange / 2), maxY];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-4">
      {/* Header and Comparison */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <span>Productivity Trends</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-normal">
              {trends.interval} aggregation ({trends.timezone})
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Range: {trends.period_start} to {trends.period_end}
          </p>
        </div>

        {/* Period Comparison Badges */}
        <div className="flex items-center gap-3 text-xs">
          <div className="px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center gap-2">
            <span className="text-slate-400">Completions:</span>
            <span className="font-semibold text-white">
              {comparison.current_period_completions} vs {comparison.prior_period_completions}
            </span>
            {comparison.completion_change_percentage !== null && (
              <span
                className={`flex items-center font-bold ${
                  comparison.completion_change_percentage >= 0
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                }`}
              >
                {comparison.completion_change_percentage >= 0 ? (
                  <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
                ) : (
                  <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                )}
                {comparison.completion_change_percentage > 0 ? '+' : ''}
                {comparison.completion_change_percentage}%
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs pt-1">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-indigo-400 rounded" />
          <span className="text-slate-300 font-medium">Created</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-emerald-400 rounded" />
          <span className="text-slate-300 font-medium">Gross Completed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-amber-400 rounded" />
          <span className="text-slate-300 font-medium">Reopened</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-teal-400 rounded border-b border-teal-200" />
          <span className="text-slate-300 font-medium">Net Completions</span>
        </div>
        {minY < 0 && (
          <span className="text-[11px] text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
            Negative net values present (reopened &gt; completed)
          </span>
        )}
      </div>

      {/* SVG Chart Container */}
      <div className="relative overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-64 select-none"
          preserveAspectRatio="none"
        >
          {/* Y Axis Grid lines */}
          {yTicks.map((tickVal, idx) => {
            const y = getY(tickVal);
            return (
              <g key={idx}>
                <line
                  x1={margin.left}
                  y1={y}
                  x2={width - margin.right}
                  y2={y}
                  stroke="#334155"
                  strokeDasharray="3 3"
                  strokeWidth="1"
                />
                <text
                  x={margin.left - 8}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="end"
                >
                  {tickVal}
                </text>
              </g>
            );
          })}

          {/* Zero baseline highlight if negative net values exist */}
          {minY < 0 && (
            <line
              x1={margin.left}
              y1={zeroY}
              x2={width - margin.right}
              y2={zeroY}
              stroke="#e2e8f0"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
          )}

          {/* Paths */}
          <path
            d={createdPath}
            fill="none"
            stroke="#818cf8"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={grossPath}
            fill="none"
            stroke="#34d399"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={reopenedPath}
            fill="none"
            stroke="#fbbf24"
            strokeWidth="2"
            strokeDasharray="4 3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={netPath}
            fill="none"
            stroke="#2dd4bf"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Interactive vertical hover lines and points */}
          {buckets.map((b, i) => {
            const cx = getX(i);
            const isHovered = hoveredBucket?.bucket_label === b.bucket_label;

            return (
              <g
                key={b.bucket_label}
                className="cursor-pointer"
                onMouseEnter={(e) => {
                  setHoveredBucket(b);
                  const rect = e.currentTarget.getBoundingClientRect();
                  setTooltipPos({ x: rect.left + rect.width / 2, y: rect.top });
                }}
                onMouseLeave={() => setHoveredBucket(null)}
              >
                {/* Invisible hover capture rect */}
                <rect
                  x={cx - innerWidth / (buckets.length * 2 || 1)}
                  y={margin.top}
                  width={innerWidth / (buckets.length || 1)}
                  height={innerHeight}
                  fill="transparent"
                />

                {isHovered && (
                  <line
                    x1={cx}
                    y1={margin.top}
                    x2={cx}
                    y2={margin.top + innerHeight}
                    stroke="#94a3b8"
                    strokeWidth="1.5"
                  />
                )}

                {/* Net completions point */}
                <circle
                  cx={cx}
                  y={getY(b.net_completions)}
                  r={isHovered ? 5 : 3.5}
                  fill={b.net_completions < 0 ? '#f43f5e' : '#2dd4bf'}
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />

                {/* X Axis labels (sample up to 8 evenly distributed labels) */}
                {(i === 0 ||
                  i === buckets.length - 1 ||
                  i % Math.ceil(buckets.length / 7) === 0) && (
                  <text
                    x={cx}
                    y={height - margin.bottom + 18}
                    fill="#94a3b8"
                    fontSize="10"
                    textAnchor="middle"
                  >
                    {b.bucket_label.length > 10
                      ? b.bucket_label.slice(5)
                      : b.bucket_label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip overlay */}
        {hoveredBucket && (
          <div
            className="absolute z-20 pointer-events-none p-3 rounded-xl bg-slate-900 border border-slate-700 shadow-xl text-xs space-y-1.5"
            style={{
              left: tooltipPos ? `${Math.min(Math.max(tooltipPos.x - 100, 20), 550)}px` : '50%',
              top: '10px',
            }}
          >
            <div className="font-semibold text-white border-b border-slate-800 pb-1">
              {hoveredBucket.bucket_label} ({hoveredBucket.start_date} ~ {hoveredBucket.end_date})
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-0.5">
              <span className="text-indigo-400">Created:</span>
              <span className="text-right font-medium text-white">
                {hoveredBucket.created_count}
              </span>
              <span className="text-emerald-400">Gross Completed:</span>
              <span className="text-right font-medium text-white">
                {hoveredBucket.gross_completions}
              </span>
              <span className="text-amber-400">Reopened:</span>
              <span className="text-right font-medium text-white">
                {hoveredBucket.reopened_count}
              </span>
              <span
                className={
                  hoveredBucket.net_completions < 0 ? 'text-rose-400' : 'text-teal-400'
                }
              >
                Net Completions:
              </span>
              <span
                className={`text-right font-bold ${
                  hoveredBucket.net_completions < 0
                    ? 'text-rose-400'
                    : 'text-teal-400'
                }`}
              >
                {hoveredBucket.net_completions}
              </span>
              <span className="text-slate-400">Unique Tasks:</span>
              <span className="text-right font-medium text-slate-300">
                {hoveredBucket.unique_tasks_completed}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Historical completeness note */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400">
        <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span className="truncate">{trends.historical_completeness_note}</span>
      </div>
    </div>
  );
};

