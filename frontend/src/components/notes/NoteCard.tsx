import React from 'react';
import { Note } from '../../types/note';
import { Pin, Archive, Trash2, Calendar, Folder, CheckSquare } from 'lucide-react';

interface NoteCardProps {
  note: Note;
  isSelected: boolean;
  onSelect: (note: Note) => void;
  onTogglePin: (note: Note) => void;
  onToggleArchive: (note: Note) => void;
  onDelete: (note: Note) => void;
}

export const NoteCard: React.FC<NoteCardProps> = ({
  note,
  isSelected,
  onSelect,
  onTogglePin,
  onToggleArchive,
  onDelete,
}) => {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div
      onClick={() => onSelect(note)}
      className={`group relative p-3.5 rounded-xl border transition-all duration-200 cursor-pointer ${
        isSelected
          ? 'bg-slate-800/90 border-emerald-500/50 shadow-md shadow-emerald-950/20'
          : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/90'
      }`}
    >
      {/* Top Header: Title & Pin/Archive/Delete actions */}
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <h4 className="text-sm font-semibold text-slate-100 line-clamp-1 flex-1 group-hover:text-emerald-400 transition">
          {note.title || 'Untitled Note'}
        </h4>

        <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onTogglePin(note);
            }}
            className={`p-1 rounded hover:bg-slate-800 transition ${
              note.is_pinned ? 'text-amber-400' : 'text-slate-500 hover:text-slate-300'
            }`}
            title={note.is_pinned ? 'Unpin note' : 'Pin note'}
            aria-label={note.is_pinned ? 'Unpin note' : 'Pin note'}
          >
            <Pin className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleArchive(note);
            }}
            className={`p-1 rounded hover:bg-slate-800 transition ${
              note.is_archived ? 'text-purple-400' : 'text-slate-500 hover:text-slate-300'
            }`}
            title={note.is_archived ? 'Restore note' : 'Archive note'}
            aria-label={note.is_archived ? 'Restore note' : 'Archive note'}
          >
            <Archive className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(note);
            }}
            className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition"
            title="Delete note"
            aria-label={`Delete note ${note.title}`}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Snippet */}
      <p className="text-xs text-slate-400 line-clamp-2 mb-2 font-normal leading-relaxed">
        {note.content.replace(/[#*`_~[\]()]/g, '') || 'No content'}
      </p>

      {/* Tags & Badges */}
      <div className="flex items-center gap-1.5 flex-wrap mb-2">
        {note.category && (
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium border bg-slate-950/60"
            style={{
              borderColor: note.category.color ? `${note.category.color}40` : '#334155',
              color: note.category.color || '#94a3b8',
            }}
          >
            {note.category.name}
          </span>
        )}
        {note.tags &&
          note.tags.map((t) => (
            <span
              key={t.id}
              className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/80 text-slate-400 border border-slate-700/50"
            >
              #{t.name}
            </span>
          ))}
      </div>

      {/* Footer: Associations & Updated At */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-800/50">
        <div className="flex items-center gap-2 truncate">
          {note.project && (
            <span className="flex items-center gap-1 text-slate-400 truncate max-w-[90px]" title={`Project: ${note.project.name}`}>
              <Folder className="w-3 h-3 text-emerald-400 shrink-0" />
              <span className="truncate">{note.project.name}</span>
            </span>
          )}
          {note.task && (
            <span className="flex items-center gap-1 text-slate-400 truncate max-w-[90px]" title={`Task: ${note.task.title}`}>
              <CheckSquare className="w-3 h-3 text-blue-400 shrink-0" />
              <span className="truncate">{note.task.title}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <Calendar className="w-3 h-3" />
          <span>{formatDate(note.updated_at)}</span>
        </div>
      </div>
    </div>
  );
};

