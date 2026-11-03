import React, { useState } from 'react';
import { Category, CategoryCreatePayload } from '../../types/category';

interface CategoryManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  onCreateCategory: (payload: CategoryCreatePayload) => Promise<void>;
  onDeleteCategory: (categoryId: string) => Promise<void>;
}

const PRESET_COLORS = [
  '#10B981', // Emerald
  '#0D9488', // Teal
  '#3B82F6', // Blue
  '#6366F1', // Indigo
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#F59E0B', // Amber
  '#EF4444', // Red
];

export const CategoryManager: React.FC<CategoryManagerModalProps> = ({
  isOpen,
  onClose,
  categories,
  onCreateCategory,
  onDeleteCategory,
}) => {
  const [name, setName] = useState('');
  const [color, setColor] = useState('#10B981');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Category name is required.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreateCategory({
        name: name.trim(),
        color,
        description: description.trim() || undefined,
      });
      setName('');
      setDescription('');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axErr = err as { response?: { data?: { detail?: string } } };
        setError(axErr.response?.data?.detail || 'Failed to create category.');
      } else {
        setError('Failed to create category.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Manage Categories</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Existing Categories List */}
        <div className="mb-6 max-h-48 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
          {categories.length === 0 ? (
            <p className="text-sm text-gray-500 py-3 text-center">No categories created yet.</p>
          ) : (
            categories.map((cat) => (
              <div key={cat.id} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="w-3.5 h-3.5 rounded-full"
                    style={{ backgroundColor: cat.color }}
                  />
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                      {cat.name}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">
                      ({cat.task_count} {cat.task_count === 1 ? 'task' : 'tasks'})
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => onDeleteCategory(cat.id)}
                  className="text-red-500 hover:text-red-700 text-xs px-2 py-1 rounded"
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>

        {/* New Category Form */}
        <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">
            Add New Category
          </h3>
          <div className="space-y-3">
            <div>
              <input
                type="text"
                placeholder="Category Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Color</label>
              <div className="flex items-center gap-2">
                {PRESET_COLORS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setColor(preset)}
                    className={`w-6 h-6 rounded-full border-2 transition-transform ${
                      color.toUpperCase() === preset.toUpperCase()
                        ? 'scale-125 border-gray-900 dark:border-white'
                        : 'border-transparent'
                    }`}
                    style={{ backgroundColor: preset }}
                  />
                ))}
              </div>
            </div>
            <div>
              <input
                type="text"
                placeholder="Description (Optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              Done
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add Category'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

