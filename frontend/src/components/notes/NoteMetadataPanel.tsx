import React from 'react';
import { Note } from '../../types/note';
import { Project } from '../../types/project';
import { Task } from '../../types/task';
import { Category } from '../../types/category';
import { Tag } from '../../types/tag';
import { TagSelector } from '../tags/TagSelector';
import { Folder, CheckSquare, Tag as TagIcon, X } from 'lucide-react';

interface NoteMetadataPanelProps {
  note: Note;
  projects: Project[];
  tasks: Task[];
  categories: Category[];
  allTags: Tag[];
  onUpdateMetadata: (updates: {
    category_id?: string | null;
    project_id?: string | null;
    task_id?: string | null;
    tag_ids?: string[];
  }) => void;
}

export const NoteMetadataPanel: React.FC<NoteMetadataPanelProps> = ({
  note,
  projects,
  tasks,
  categories,
  allTags,
  onUpdateMetadata,
}) => {
  const selectedTagIds = note.tags ? note.tags.map((t) => t.id) : [];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-xl backdrop-blur-md space-y-4 text-xs">
      <h3 className="font-semibold text-slate-200 text-sm border-b border-slate-800/80 pb-2">
        Note Details & Links
      </h3>

      {/* Category selector */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium">Category</label>
        <div className="flex items-center gap-1.5">
          <select
            value={note.category_id || ''}
            onChange={(e) =>
              onUpdateMetadata({ category_id: e.target.value ? e.target.value : null })
            }
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">No Category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {note.category_id && (
            <button
              onClick={() => onUpdateMetadata({ category_id: null })}
              className="p-1.5 text-slate-400 hover:text-rose-400"
              title="Remove category"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Project association */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium flex items-center gap-1">
          <Folder className="w-3.5 h-3.5 text-emerald-400" />
          <span>Associated Project</span>
        </label>
        <div className="flex items-center gap-1.5">
          <select
            value={note.project_id || ''}
            onChange={(e) =>
              onUpdateMetadata({ project_id: e.target.value ? e.target.value : null })
            }
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">None</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          {note.project_id && (
            <button
              onClick={() => onUpdateMetadata({ project_id: null })}
              className="p-1.5 text-slate-400 hover:text-rose-400"
              title="Remove project link"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Task association */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium flex items-center gap-1">
          <CheckSquare className="w-3.5 h-3.5 text-blue-400" />
          <span>Associated Task</span>
        </label>
        <div className="flex items-center gap-1.5">
          <select
            value={note.task_id || ''}
            onChange={(e) =>
              onUpdateMetadata({ task_id: e.target.value ? e.target.value : null })
            }
            className="flex-1 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">None</option>
            {tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>
          {note.task_id && (
            <button
              onClick={() => onUpdateMetadata({ task_id: null })}
              className="p-1.5 text-slate-400 hover:text-rose-400"
              title="Remove task link"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Tags selector */}
      <div>
        <label className="block text-slate-400 mb-1 font-medium flex items-center gap-1">
          <TagIcon className="w-3.5 h-3.5 text-purple-400" />
          <span>Tags</span>
        </label>
        <TagSelector
          tags={allTags || []}
          selectedTagIds={selectedTagIds}
          onChange={(newTagIds) => onUpdateMetadata({ tag_ids: newTagIds })}
        />
      </div>
    </div>
  );
};
