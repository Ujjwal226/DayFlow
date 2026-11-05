import React from 'react';

const WEEKDAYS = [
  { value: 0, label: 'Mon', fullLabel: 'Monday' },
  { value: 1, label: 'Tue', fullLabel: 'Tuesday' },
  { value: 2, label: 'Wed', fullLabel: 'Wednesday' },
  { value: 3, label: 'Thu', fullLabel: 'Thursday' },
  { value: 4, label: 'Fri', fullLabel: 'Friday' },
  { value: 5, label: 'Sat', fullLabel: 'Saturday' },
  { value: 6, label: 'Sun', fullLabel: 'Sunday' },
];

interface WeeklyScheduleSelectorProps {
  selectedWeekdays: number[];
  onChange: (weekdays: number[]) => void;
  disabled?: boolean;
}

export const WeeklyScheduleSelector: React.FC<WeeklyScheduleSelectorProps> = ({
  selectedWeekdays,
  onChange,
  disabled = false,
}) => {
  const toggleWeekday = (day: number) => {
    if (disabled) return;
    if (selectedWeekdays.includes(day)) {
      // Don't allow deselecting the last weekday
      if (selectedWeekdays.length === 1) return;
      onChange(selectedWeekdays.filter((d) => d !== day));
    } else {
      onChange([...selectedWeekdays, day].sort((a, b) => a - b));
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-slate-300">
        Repeat on Weekdays <span className="text-emerald-400">*</span>
      </label>
      <div className="flex items-center gap-1.5 flex-wrap">
        {WEEKDAYS.map((day) => {
          const isSelected = selectedWeekdays.includes(day.value);
          return (
            <button
              key={day.value}
              type="button"
              disabled={disabled}
              onClick={() => toggleWeekday(day.value)}
              title={day.fullLabel}
              className={`w-9 h-9 rounded-lg text-xs font-semibold transition flex items-center justify-center border ${
                isSelected
                  ? 'bg-emerald-500 text-white border-emerald-400 shadow-sm shadow-emerald-500/20'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {day.label}
            </button>
          );
        })}
      </div>
      <p className="text-[11px] text-slate-400">
        Select one or more days of the week on which this task repeats.
      </p>
    </div>
  );
};

