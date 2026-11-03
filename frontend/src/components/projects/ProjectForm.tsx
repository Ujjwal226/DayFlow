import React, { useState } from 'react';
import { Project, ProjectCreatePayload, ProjectPriority, ProjectStatus } from '../../types/project';

interface ProjectFormProps {
  initialProject?: Project | null;
  onSubmit: (payload: ProjectCreatePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const PRESET_COLORS = [
  '#3B82F6', // Blue
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#64748B', // Slate
];

export const ProjectForm: React.FC<ProjectFormProps> = ({
  initialProject,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [name, setName] = useState(initialProject?.name || '');
  const [description, setDescription] = useState(initialProject?.description || '');
  const [status, setStatus] = useState<ProjectStatus>(initialProject?.status || 'PLANNED');
  const [priority, setPriority] = useState<ProjectPriority>(initialProject?.priority || 'MEDIUM');
  const [startDate, setStartDate] = useState(initialProject?.start_date || '');
  const [dueDate, setDueDate] = useState(initialProject?.due_date || '');
  const [color, setColor] = useState(initialProject?.color || '#3B82F6');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Project name is required.');
      return;
    }

    if (startDate && dueDate && dueDate < startDate) {
      setError('Due date cannot be earlier than start date.');
      return;
    }

    try {
      await onSubmit({
        name: trimmedName,
        description: description.trim() || null,
        status,
        priority,
        start_date: startDate || null,
        due_date: dueDate || null,
        color: color || null,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to save project.');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="project-name" className="block text-xs font-medium text-gray-700 mb-1">
          Project Name *
        </label>
        <input
          id="project-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={150}
          required
          placeholder="e.g., Website Redesign"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="project-desc" className="block text-xs font-medium text-gray-700 mb-1">
          Description (Optional)
        </label>
        <textarea
          id="project-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="What is the goal of this project?"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="project-status" className="block text-xs font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id="project-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as ProjectStatus)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="PLANNED">Planned</option>
            <option value="ACTIVE">Active</option>
            <option value="ON_HOLD">On Hold</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>

        <div>
          <label htmlFor="project-priority" className="block text-xs font-medium text-gray-700 mb-1">
            Priority
          </label>
          <select
            id="project-priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as ProjectPriority)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="project-start-date" className="block text-xs font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            id="project-start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="project-due-date" className="block text-xs font-medium text-gray-700 mb-1">
            Due Date
          </label>
          <input
            id="project-due-date"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1.5">Color Accent</label>
        <div className="flex items-center gap-2 flex-wrap">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className={`w-6 h-6 rounded-full border-2 transition-transform ${
                color === c ? 'border-gray-900 scale-110 shadow-sm' : 'border-transparent hover:scale-105'
              }`}
              style={{ backgroundColor: c }}
              title={c}
            />
          ))}
          <input
            type="text"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            maxLength={7}
            placeholder="#3B82F6"
            className="w-24 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 uppercase font-mono"
          />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : initialProject ? 'Save Changes' : 'Create Project'}
        </button>
      </div>
    </form>
  );
};

