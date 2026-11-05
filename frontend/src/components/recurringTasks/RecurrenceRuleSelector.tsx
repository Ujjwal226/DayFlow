import React from 'react';
import { RecurrenceFrequency } from '../../types/recurringTask';
import { WeeklyScheduleSelector } from './WeeklyScheduleSelector';

interface RecurrenceRuleSelectorProps {
  frequency: RecurrenceFrequency;
  interval: number;
  weekdays: number[];
  dayOfMonth: number | null;
  monthOfYear: number | null;
  onFrequencyChange: (freq: RecurrenceFrequency) => void;
  onIntervalChange: (interval: number) => void;
  onWeekdaysChange: (weekdays: number[]) => void;
  onDayOfMonthChange: (dom: number | null) => void;
  onMonthOfYearChange: (moy: number | null) => void;
  disabled?: boolean;
}

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
];

export const RecurrenceRuleSelector: React.FC<RecurrenceRuleSelectorProps> = ({
  frequency,
  interval,
  weekdays,
  dayOfMonth,
  monthOfYear,
  onFrequencyChange,
  onIntervalChange,
  onWeekdaysChange,
  onDayOfMonthChange,
  onMonthOfYearChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      {/* Frequency & Interval row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Recurrence Frequency <span className="text-emerald-400">*</span>
          </label>
          <select
            value={frequency}
            disabled={disabled}
            onChange={(e) => onFrequencyChange(e.target.value as RecurrenceFrequency)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
          >
            <option value="DAILY">Daily</option>
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="YEARLY">Yearly</option>
            <option value="CUSTOM">Custom Interval</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            {frequency === 'DAILY' && 'Repeat Every (Days)'}
            {frequency === 'WEEKLY' && 'Repeat Every (Weeks)'}
            {frequency === 'MONTHLY' && 'Repeat Every (Months)'}
            {frequency === 'YEARLY' && 'Repeat Every (Years)'}
            {frequency === 'CUSTOM' && 'Interval (Days)'}
          </label>
          <input
            type="number"
            min={1}
            max={365}
            value={interval}
            disabled={disabled}
            onChange={(e) => onIntervalChange(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
          />
        </div>
      </div>

      {/* Frequency-specific options */}
      {frequency === 'WEEKLY' && (
        <WeeklyScheduleSelector
          selectedWeekdays={weekdays}
          onChange={onWeekdaysChange}
          disabled={disabled}
        />
      )}

      {frequency === 'MONTHLY' && (
        <div className="space-y-2">
          <label className="block text-xs font-medium text-slate-300">
            Day of Month
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <select
              value={dayOfMonth === null ? '' : dayOfMonth}
              disabled={disabled}
              onChange={(e) => {
                const val = e.target.value;
                onDayOfMonthChange(val === '' ? null : parseInt(val));
              }}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">Start date's day of month</option>
              <option value="-1">Last day of month (-1)</option>
              {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                <option key={d} value={d}>
                  Day {d}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 self-center">
              Months with fewer days will clamp safely to the last day of the month.
            </p>
          </div>
        </div>
      )}

      {frequency === 'YEARLY' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Month of Year
            </label>
            <select
              value={monthOfYear === null ? '' : monthOfYear}
              disabled={disabled}
              onChange={(e) => {
                const val = e.target.value;
                onMonthOfYearChange(val === '' ? null : parseInt(val));
              }}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">Start date's month</option>
              {MONTHS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Day of Month
            </label>
            <select
              value={dayOfMonth === null ? '' : dayOfMonth}
              disabled={disabled}
              onChange={(e) => {
                const val = e.target.value;
                onDayOfMonthChange(val === '' ? null : parseInt(val));
              }}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">Start date's day</option>
              <option value="-1">Last day of month (-1)</option>
              {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                <option key={d} value={d}>
                  Day {d}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

