import React from 'react';
import {
  Repeat,
  CheckCircle2,
  Clock,
  Calendar,
  FastForward,
  CheckCheck,
  Percent,
  Info,
} from 'lucide-react';
import { RecurringAnalyticsResponse } from '../../types/analytics';

interface RecurringInsightsSectionProps {
  recurringData: RecurringAnalyticsResponse | null;
  loading: boolean;
}

export const RecurringInsightsSection: React.FC<RecurringInsightsSectionProps> = ({
  recurringData,
  loading,
}) => {
  if (loading && !recurringData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse h-56 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading recurring insights...</span>
      </div>
    );
  }

  if (!recurringData) {
    return null;
  }

  const {
    total_series,
    active_series,
    paused_or_stopped_series,
    total_generated_occurrences,
    completed_occurrences,
    pending_due_occurrences,
    future_occurrences,
    skipped_occurrences,
    eligible_due_occurrences,
    adherence_rate,
    frequency_breakdown,
    schema_limitations_note,
  } = recurringData;

  const frequencies = [
    { label: 'Daily', count: frequency_breakdown.daily },
    { label: 'Weekly', count: frequency_breakdown.weekly },
    { label: 'Monthly', count: frequency_breakdown.monthly },
    { label: 'Yearly', count: frequency_breakdown.yearly },
    { label: 'Custom', count: frequency_breakdown.custom },
  ];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Repeat className="w-4 h-4 text-emerald-400" />
            <span>Recurring Task Insights</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-normal">
              {total_series} series ({active_series} active, {paused_or_stopped_series} paused/stopped)
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Adherence calculation across materialized due occurrences and deliberate skips.
          </p>
        </div>

        {/* Adherence Rate Badge */}
        <div className="px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2.5 self-start sm:self-auto">
          <Percent className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-[10px] text-emerald-400/80 block uppercase tracking-wider font-semibold">
              Adherence Rate
            </span>
            <span className="text-base font-bold text-white">
              {adherence_rate}%
            </span>
          </div>
        </div>
      </div>

      {total_series === 0 && total_generated_occurrences === 0 ? (
        <div className="p-8 rounded-xl border border-dashed border-slate-800 text-center space-y-1">
          <p className="text-sm font-medium text-slate-400">No recurring series created</p>
          <p className="text-xs text-slate-500">
            Set up recurring tasks to monitor schedule adherence and habit completion trends.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Occurrence Breakdown Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col justify-between">
              <span className="text-[11px] text-slate-400">Materialized</span>
              <span className="text-lg font-bold text-white mt-1">
                {total_generated_occurrences}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/40 border border-emerald-500/20 flex flex-col justify-between">
              <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Completed
              </span>
              <span className="text-lg font-bold text-emerald-400 mt-1">
                {completed_occurrences}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/40 border border-amber-500/20 flex flex-col justify-between">
              <span className="text-[11px] text-amber-400 flex items-center gap-1">
                <Clock className="w-3 h-3" /> Pending Due
              </span>
              <span className="text-lg font-bold text-amber-400 mt-1">
                {pending_due_occurrences}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/40 border border-indigo-500/20 flex flex-col justify-between">
              <span className="text-[11px] text-indigo-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Future (Excluded)
              </span>
              <span className="text-lg font-bold text-indigo-400 mt-1">
                {future_occurrences}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-700 flex flex-col justify-between">
              <span className="text-[11px] text-slate-300 flex items-center gap-1">
                <FastForward className="w-3 h-3 text-slate-400" /> Skipped
              </span>
              <span className="text-lg font-bold text-slate-200 mt-1">
                {skipped_occurrences}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/40 border border-teal-500/20 flex flex-col justify-between">
              <span className="text-[11px] text-teal-400 flex items-center gap-1">
                <CheckCheck className="w-3 h-3" /> Eligible Due
              </span>
              <span className="text-lg font-bold text-teal-400 mt-1">
                {eligible_due_occurrences}
              </span>
            </div>
          </div>

          {/* Recurrence Frequency Distribution */}
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="text-slate-400 font-medium">Frequency Breakdown:</span>
            <div className="flex flex-wrap items-center gap-2">
              {frequencies.map((f) => (
                <div
                  key={f.label}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-1.5"
                >
                  <span className="text-slate-400">{f.label}:</span>
                  <span className="font-semibold text-white">{f.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Schema limitations note */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">{schema_limitations_note}</span>
          </div>
        </div>
      )}
    </div>
  );
};

