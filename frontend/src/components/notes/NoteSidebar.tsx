import React from 'react';
import { Category } from '../../types/category';
import { Tag } from '../../types/tag';
import { Search, Plus, Pin, Archive, Tag as TagIcon, X } from 'lucide-react';

interface NoteSidebarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCategory: string | 'ALL';
  onCategoryChange: (catId: string | 'ALL') => void;
  selectedTag: string | 'ALL';
  onTagChange: (tagId: string | 'ALL') => void;
  filterView: 'active' | 'archived';
  onFilterViewChange: (view: 'active' | 'archived') => void;
  categories: Category[];
  tags: Tag[];
  onNewNote: () => void;
}

export const NoteSidebar: React.FC<NoteSidebarProps> = ({
  searchQuery,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
  selectedTag,
  onTagChange,
  filterView,
  onFilterViewChange,
  categories,
  tags,
  onNewNote,
}) => {
  return (
    <div className="space-y-4">
      {/* Top Action: New Note Button */}
      <button
        onClick={onNewNote}
        className="w-full py-2.5 px-4 bg-emerald-500 hover:bg-emerald-600 active:scale-[0.99] text-slate-950 font-semibold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition"
      >
        <Plus className="w-4 h-4" />
        <span>New Note</span>
      </button>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-8 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Navigation: Active vs. Archived */}
      <div className="flex rounded-xl bg-slate-900/60 p-1 border border-slate-800 text-xs">
        <button
          onClick={() => onFilterViewChange('active')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition flex items-center justify-center gap-1.5 ${
            filterView === 'active'
              ? 'bg-slate-800 text-emerald-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Pin className="w-3.5 h-3.5" />
          <span>Active</span>
        </button>
        <button
          onClick={() => onFilterViewChange('archived')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition flex items-center justify-center gap-1.5 ${
            filterView === 'archived'
              ? 'bg-slate-800 text-purple-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Archive className="w-3.5 h-3.5" />
          <span>Archived</span>
        </button>
      </div>

      {/* Categories Filter */}
      {categories.length > 0 && (
        <div className="space-y-1">
          <label className="text-[11px] font-semibold text-slate-400 px-1 uppercase tracking-wider">
            Categories
          </label>
          <div className="space-y-0.5">
            <button
              onClick={() => onCategoryChange('ALL')}
              className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition ${
                selectedCategory === 'ALL'
                  ? 'bg-slate-800 text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
              }`}
            >
              All Categories
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => onCategoryChange(c.id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition flex items-center gap-2 ${
                  selectedCategory === c.id
                    ? 'bg-slate-800 text-slate-100 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: c.color }}
                />
                <span className="truncate">{c.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tags Filter */}
      {tags.length > 0 && (
        <div className="space-y-1">
          <label className="text-[11px] font-semibold text-slate-400 px-1 uppercase tracking-wider flex items-center gap-1">
            <TagIcon className="w-3 h-3" />
            <span>Tags</span>
          </label>
          <div className="flex flex-wrap gap-1 p-1">
            <button
              onClick={() => onTagChange('ALL')}
              className={`px-2 py-0.5 rounded text-[11px] transition ${
                selectedTag === 'ALL'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              All
            </button>
            {tags.map((t) => (
              <button
                key={t.id}
                onClick={() => onTagChange(t.id)}
                className={`px-2 py-0.5 rounded text-[11px] transition ${
                  selectedTag === t.id
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                #{t.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

