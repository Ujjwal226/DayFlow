import React, { useState } from 'react';
import { Subtask, SubtaskUpdatePayload } from '../../types/subtask';

interface SubtaskItemProps {
  subtask: Subtask;
  onUpdate: (subtaskId: string, payload: SubtaskUpdatePayload) => Promise<void>;
  onDelete: (subtaskId: string) => Promise<void>;
}

export const SubtaskItem: React.FC<SubtaskItemProps> = ({ subtask, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(subtask.title);
  const isCompleted = subtask.status === 'COMPLETED';

  const handleToggleCompleted = async () => {
    await onUpdate(subtask.id, {
      status: isCompleted ? 'TODO' : 'COMPLETED',
    });
  };

  const handleSaveEdit = async () => {
    if (!title.trim() || title === subtask.title) {
      setIsEditing(false);
      return;
    }
    await onUpdate(subtask.id, { title: title.trim() });
    setIsEditing(false);
  };

  return (
    <div className="flex items-center justify-between py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-750 rounded-lg group transition-colors">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <input
          type="checkbox"
          checked={isCompleted}
          onChange={handleToggleCompleted}
          className="w-4 h-4 text-emerald-600 rounded border-gray-300 dark:border-gray-600 focus:ring-emerald-500 cursor-pointer"
        />

        {isEditing ? (
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleSaveEdit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveEdit();
              if (e.key === 'Escape') {
                setTitle(subtask.title);
                setIsEditing(false);
              }
            }}
            autoFocus
            className="text-sm px-2 py-0.5 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white flex-1"
          />
        ) : (
          <span
            onClick={() => setIsEditing(true)}
            className={`text-sm cursor-pointer truncate ${
              isCompleted
                ? 'line-through text-gray-400 dark:text-gray-500'
                : 'text-gray-800 dark:text-gray-200'
            }`}
          >
            {subtask.title}
          </span>
        )}
      </div>

      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
        <button
          type="button"
          onClick={() => setIsEditing(!isEditing)}
          className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 px-1.5 py-0.5"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => onDelete(subtask.id)}
          className="text-xs text-red-500 hover:text-red-700 px-1.5 py-0.5"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

