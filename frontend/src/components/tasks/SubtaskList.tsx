import React, { useState } from 'react';
import { Subtask, SubtaskCreatePayload, SubtaskUpdatePayload } from '../../types/subtask';
import { SubtaskItem } from './SubtaskItem';

interface SubtaskListProps {
  parentTaskId: string;
  subtasks: Subtask[];
  onCreateSubtask: (parentTaskId: string, payload: SubtaskCreatePayload) => Promise<void>;
  onUpdateSubtask: (subtaskId: string, payload: SubtaskUpdatePayload) => Promise<void>;
  onDeleteSubtask: (subtaskId: string) => Promise<void>;
}

export const SubtaskList: React.FC<SubtaskListProps> = ({
  parentTaskId,
  subtasks,
  onCreateSubtask,
  onUpdateSubtask,
  onDeleteSubtask,
}) => {
  const [newTitle, setNewTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddSubtask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setIsSubmitting(true);
    try {
      await onCreateSubtask(parentTaskId, { title: newTitle.trim() });
      setNewTitle('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="divide-y divide-gray-100 dark:divide-gray-700">
        {subtasks.map((subtask) => (
          <SubtaskItem
            key={subtask.id}
            subtask={subtask}
            onUpdate={onUpdateSubtask}
            onDelete={onDeleteSubtask}
          />
        ))}
      </div>

      <form onSubmit={handleAddSubtask} className="flex gap-2 pt-2">
        <input
          type="text"
          placeholder="Add a subtask..."
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          className="flex-1 text-sm px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
        />
        <button
          type="submit"
          disabled={isSubmitting || !newTitle.trim()}
          className="px-3 py-1.5 text-xs font-medium text-white bg-teal-600 hover:bg-teal-700 rounded-lg disabled:opacity-50"
        >
          {isSubmitting ? 'Adding...' : 'Add'}
        </button>
      </form>
    </div>
  );
};

