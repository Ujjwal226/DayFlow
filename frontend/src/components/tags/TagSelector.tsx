import React from 'react';
import { Tag } from '../../types/tag';

interface TagSelectorProps {
  tags: Tag[];
  selectedTagIds: string[];
  onChange: (newTagIds: string[]) => void;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  tags,
  selectedTagIds,
  onChange,
}) => {
  const toggleTag = (id: string) => {
    if (selectedTagIds.includes(id)) {
      onChange(selectedTagIds.filter((tId) => tId !== id));
    } else {
      onChange([...selectedTagIds, id]);
    }
  };

  if (tags.length === 0) {
    return (
      <p className="text-xs text-gray-500 italic">No tags available. Create tags first.</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((tag) => {
        const isSelected = selectedTagIds.includes(tag.id);
        const color = tag.color || '#0D9488';
        return (
          <button
            key={tag.id}
            type="button"
            onClick={() => toggleTag(tag.id)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              isSelected
                ? 'text-white border-transparent'
                : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-gray-300'
            }`}
            style={isSelected ? { backgroundColor: color } : undefined}
          >
            #{tag.name}
          </button>
        );
      })}
    </div>
  );
};

