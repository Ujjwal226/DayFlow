import React from 'react';
import { Category } from '../../types/category';

interface CategoryBadgeProps {
  category: Category;
  size?: 'sm' | 'md';
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-opacity-30 ${sizeClasses}`}
      style={{
        backgroundColor: `${category.color}15`,
        borderColor: category.color,
        color: category.color,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: category.color }}
      />
      <span>{category.name}</span>
    </span>
  );
};

