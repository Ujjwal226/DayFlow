import React from 'react';
import { RecurrenceFrequency } from '../../types/recurringTask';
import { Repeat } from 'lucide-react';

interface RecurrenceBadgeProps {
  frequency: RecurrenceFrequency;
  interval?: number;
  className?: string;
}

export const RecurrenceBadge: React.FC<RecurrenceBadgeProps> = ({
  frequency,
  interval = 1,
  className = '',
}) => {
  const getFrequencyLabel = () => {
    if (interval === 1) {
      switch (frequency) {
        case 'DAILY':
          return 'Daily';
        case 'WEEKLY':
          return 'Weekly';
        case 'MONTHLY':
          return 'Monthly';
        case 'YEARLY':
          return 'Yearly';
        case 'CUSTOM':
          return 'Custom';
        default:
          return frequency;
      }
    }

    switch (frequency) {
      case 'DAILY':
        return `Every ${interval} days`;
      case 'WEEKLY':
        return `Every ${interval} weeks`;
      case 'MONTHLY':
        return `Every ${interval} months`;
      case 'YEARLY':
        return `Every ${interval} years`;
      case 'CUSTOM':
        return `Every ${interval} days`;
      default:
        return `Every ${interval} (${frequency})`;
    }
  };

  const getColorClasses = () => {
    switch (frequency) {
      case 'DAILY':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'WEEKLY':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'MONTHLY':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'YEARLY':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'CUSTOM':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${getColorClasses()} ${className}`}
    >
      <Repeat className="w-3 h-3" />
      <span>{getFrequencyLabel()}</span>
    </span>
  );
};

