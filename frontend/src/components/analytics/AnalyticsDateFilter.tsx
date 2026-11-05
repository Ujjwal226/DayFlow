import React from 'react';
import { Calendar, Globe, RefreshCw } from 'lucide-react';

export type DateRangePreset = '7d' | '30d' | '90d' | 'custom';
export type AggregationInterval = 'daily' | 'weekly' | 'monthly';

interface AnalyticsDateFilterProps {
  preset: DateRangePreset;
  onPresetChange: (preset: DateRangePreset) => void;
  customStartDate: string;
  onCustomStartDateChange: (date: string) => void;
  customEndDate: string;
  onCustomEndDateChange: (date: string) => void;
  interval: AggregationInterval;
  onIntervalChange: (interval: AggregationInterval) => void;
  timezone: string;
  onTimezoneChange: (timezone: string) => void;
  onRefresh: () => void;
  loading: boolean;
}

const COMMON_TIMEZONES = [
  { label: 'Asia/Kolkata (IST)', value: 'Asia/Kolkata' },
  { label: 'UTC', value: 'UTC' },
  { label: 'America/New_York (EST/EDT)', value: 'America/New_York' },
  { label: 'America/Los_Angeles (PST/PDT)', value: 'America/Los_Angeles' },
  { label: 'Europe/London (GMT/BST)', value: 'Europe/London' },
  { label: 'Europe/Paris (CET/CEST)', value: 'Europe/Paris' },
  { label: 'Asia/Tokyo (JST)', value: 'Asia/Tokyo' },
  { label: 'Australia/Sydney (AEST)', value: 'Australia/Sydney' },
];

export const AnalyticsDateFilter: React.FC<AnalyticsDateFilterProps> = ({
  preset,
  onPresetChange,
  customStartDate,
  onCustomStartDateChange,
  customEndDate,
  onCustomEndDateChange,
  interval,
  onIntervalChange,
  timezone,
  onTimezoneChange,
  onRefresh,
  loading,
}) => {
  return (
    <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
      {/* Date Range Selector */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-1">
          <Calendar className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-medium">Range:</span>
        </div>

        <div className="flex items-center rounded-xl bg-slate-950 p-1 border border-slate-800">
          <button
            onClick={() => onPresetChange('7d')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
              preset === '7d'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => onPresetChange('30d')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
              preset === '30d'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => onPresetChange('90d')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
              preset === '90d'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            90 Days
          </button>
          <button
            onClick={() => onPresetChange('custom')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
              preset === 'custom'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Custom
          </button>
        </div>

        {/* Custom Start & End Date inputs */}
        {preset === 'custom' && (
          <div className="flex flex-wrap items-center gap-2 ml-1">
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => onCustomStartDateChange(e.target.value)}
              className="px-2.5 py-1 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-emerald-500"
              aria-label="Start Date"
            />
            <span className="text-slate-500 text-xs">to</span>
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => onCustomEndDateChange(e.target.value)}
              className="px-2.5 py-1 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-emerald-500"
              aria-label="End Date"
            />
            {customStartDate && customEndDate && customStartDate > customEndDate && (
              <span className="text-[11px] text-rose-400 font-medium ml-1">
                Start date cannot be after end date
              </span>
            )}
          </div>
        )}
      </div>

      {/* Interval, Timezone and Refresh actions */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Aggregation interval */}
        <div className="flex items-center rounded-xl bg-slate-950 p-1 border border-slate-800">
          <button
            onClick={() => onIntervalChange('daily')}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              interval === 'daily'
                ? 'bg-indigo-500/20 text-indigo-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => onIntervalChange('weekly')}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              interval === 'weekly'
                ? 'bg-indigo-500/20 text-indigo-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => onIntervalChange('monthly')}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              interval === 'monthly'
                ? 'bg-indigo-500/20 text-indigo-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Monthly
          </button>
        </div>

        {/* Timezone Dropdown */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">
          <Globe className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={timezone}
            onChange={(e) => onTimezoneChange(e.target.value)}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer pr-1"
            aria-label="Select Timezone"
          >
            {COMMON_TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value} className="bg-slate-900 text-white">
                {tz.label}
              </option>
            ))}
          </select>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
          title="Refresh analytics data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
};
