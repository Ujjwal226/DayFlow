import React from 'react';
import { cn } from '../../lib/utils';
import type { Priority, Category } from '../../types/api';

interface PriorityBadgeProps {
  priority: Priority;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, className }) => {
  const styles: Record<Priority, string> = {
    high: 'bg-rose-500/10 text-rose-400 border border-rose-500/20 dark:text-rose-400 dark:bg-rose-500/10',
    medium: 'bg-amber-500/10 text-amber-500 border border-amber-500/20 dark:text-amber-400 dark:bg-amber-500/10',
    low: 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 dark:text-emerald-400 dark:bg-emerald-500/10',
  };

  const labels: Record<Priority, string> = {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium tracking-wide transition-colors',
        styles[priority],
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full mr-1.5', {
        'bg-rose-500': priority === 'high',
        'bg-amber-500': priority === 'medium',
        'bg-emerald-500': priority === 'low',
      })} />
      {labels[priority]}
    </span>
  );
};

interface CategoryBadgeProps {
  category: Category;
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, className }) => {
  const styles: Record<Category, string> = {
    work: 'bg-violet-500/10 text-violet-400 border border-violet-500/20',
    personal: 'bg-sky-500/10 text-sky-400 border border-sky-500/20',
    learning: 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20',
    health: 'bg-teal-500/10 text-teal-400 border border-teal-500/20',
    other: 'bg-slate-500/10 text-slate-400 border border-slate-500/20',
  };

  const labels: Record<Category, string> = {
    work: 'Work',
    personal: 'Personal',
    learning: 'Learning',
    health: 'Health',
    other: 'Other',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium capitalize transition-colors',
        styles[category] || styles.other,
        className
      )}
    >
      {labels[category] || category}
    </span>
  );
};
