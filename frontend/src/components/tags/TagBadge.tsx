import React from 'react';
import { Tag } from '../../types/tag';

interface TagBadgeProps {
  tag: Tag;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export const TagBadge: React.FC<TagBadgeProps> = ({ tag, size = 'sm', onRemove }) => {
  const color = tag.color || '#0D9488';
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border border-opacity-30 ${sizeClasses}`}
      style={{
        backgroundColor: `${color}15`,
        borderColor: color,
        color: color,
      }}
    >
      <span>#{tag.name}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 hover:opacity-75 focus:outline-none"
        >
          ×
        </button>
      )}
    </span>
  );
};

