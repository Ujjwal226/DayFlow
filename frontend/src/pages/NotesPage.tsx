import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { notesApi } from '../api/notes';
import { projectsApi } from '../api/projects';
import { tasksApi } from '../api/tasks';
import { categoriesApi } from '../api/categories';
import { tagsApi } from '../api/tags';
import { Note } from '../types/note';
import { Project } from '../types/project';
import { Task } from '../types/task';
import { Category } from '../types/category';
import { Tag } from '../types/tag';
import { NoteSidebar } from '../components/notes/NoteSidebar';
import { NoteCard } from '../components/notes/NoteCard';
import { NoteEditor } from '../components/notes/NoteEditor';
import { NoteMetadataPanel } from '../components/notes/NoteMetadataPanel';
import {
  FileText,
  Layers,
  Calendar,
  CheckSquare,
  Kanban as KanbanIcon,
  LogOut,
  AlertCircle,
  Pin,
  Folder,
} from 'lucide-react';

export const NotesPage: React.FC = () => {
  const { logout } = useAuth();

  // Data state
  const [notes, setNotes] = useState<Note[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active note selection and editing state
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [editorTitle, setEditorTitle] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved' | 'error'>('saved');
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | 'ALL'>('ALL');
  const [selectedTag, setSelectedTag] = useState<string | 'ALL'>('ALL');
  const [filterView, setFilterView] = useState<'active' | 'archived'>('active');

  // Debounce autosave timer ref
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch initial notes and reference records
  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [notesRes, projectsRes, tasksRes, categoriesRes, tagsRes] = await Promise.all([
        notesApi.listNotes({ page: 1, page_size: 100, is_archived: filterView === 'archived' }),
        projectsApi.list({ page_size: 100 }),
        tasksApi.listTasks({ page_size: 100, is_archived: false }),
        categoriesApi.listCategories(),
        tagsApi.listTags(),
      ]);

      setNotes(notesRes.items);
      setProjects(projectsRes.items);
      setTasks(tasksRes.items);
      setCategories(categoriesRes);
      setTags(tagsRes);

      // Select first note if none selected
      if (notesRes.items.length > 0 && !selectedNoteId) {
        const first = notesRes.items[0];
        setSelectedNoteId(first.id);
        setEditorTitle(first.title);
        setEditorContent(first.content);
        setSaveStatus('saved');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load notes workspace data.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [filterView, selectedNoteId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Find currently selected note object
  const selectedNote = useMemo(() => {
    return notes.find((n) => n.id === selectedNoteId) || null;
  }, [notes, selectedNoteId]);

  // Filter notes client-side based on sidebar controls
  const filteredNotes = useMemo(() => {
    return notes.filter((n) => {
      // Archive view filter
      if (filterView === 'archived') {
        if (!n.is_archived) return false;
      } else {
        if (n.is_archived) return false;
      }

      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = n.title.toLowerCase().includes(q);
        const matchesContent = n.content.toLowerCase().includes(q);
        if (!matchesTitle && !matchesContent) return false;
      }

      // Category
      if (selectedCategory !== 'ALL') {
        if (n.category_id !== selectedCategory) return false;
      }

      // Tag
      if (selectedTag !== 'ALL') {
        if (!n.tags || !n.tags.some((t) => t.id === selectedTag)) return false;
      }

      return true;
    });
  }, [notes, filterView, searchQuery, selectedCategory, selectedTag]);

  // Separate pinned vs regular
  const pinnedNotes = useMemo(() => {
    return filteredNotes.filter((n) => n.is_pinned);
  }, [filteredNotes]);

  const regularNotes = useMemo(() => {
    return filteredNotes.filter((n) => !n.is_pinned);
  }, [filteredNotes]);

  // Autosave executor
  const performSave = useCallback(
    async (noteId: string, title: string, content: string) => {
      setSaveStatus('saving');
      try {
        const updated = await notesApi.updateNote(noteId, {
          title: title.trim() || 'Untitled Note',
          content,
        });

        setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
        setSaveStatus('saved');
        setLastSavedAt(new Date());
      } catch {
        setSaveStatus('error');
      }
    },
    []
  );

  // Trigger autosave when title or content changes
  const handleTitleChange = (newTitle: string) => {
    setEditorTitle(newTitle);
    setSaveStatus('unsaved');

    if (!selectedNoteId) return;

    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    autosaveTimerRef.current = setTimeout(() => {
      performSave(selectedNoteId, newTitle, editorContent);
    }, 1000);
  };

  const handleContentChange = (newContent: string) => {
    setEditorContent(newContent);
    setSaveStatus('unsaved');

    if (!selectedNoteId) return;

    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    autosaveTimerRef.current = setTimeout(() => {
      performSave(selectedNoteId, editorTitle, newContent);
    }, 1000);
  };

  // Immediate explicit save
  const handleSaveExplicit = () => {
    if (!selectedNoteId) return;
    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    performSave(selectedNoteId, editorTitle, editorContent);
  };

  // Switch active note
  const handleSelectNote = (note: Note) => {
    // If unsaved changes on current, save before switching
    if (saveStatus === 'unsaved' && selectedNoteId) {
      performSave(selectedNoteId, editorTitle, editorContent);
    }
    setSelectedNoteId(note.id);
    setEditorTitle(note.title);
    setEditorContent(note.content);
    setSaveStatus('saved');
  };

  // Create new note
  const handleNewNote = async () => {
    try {
      const newNote = await notesApi.createNote({
        title: 'Untitled Note',
        content: '',
        is_pinned: false,
      });

      setNotes((prev) => [newNote, ...prev]);
      setSelectedNoteId(newNote.id);
      setEditorTitle(newNote.title);
      setEditorContent(newNote.content);
      setSaveStatus('saved');
    } catch {
      setError('Failed to create new note.');
    }
  };

  // Pin/unpin note
  const handleTogglePin = async (note: Note) => {
    try {
      const updated = await notesApi.updateNote(note.id, {
        is_pinned: !note.is_pinned,
      });
      setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
    } catch {
      setError(`Failed to update pinned state for "${note.title}".`);
    }
  };

  // Archive/restore note
  const handleToggleArchive = async (note: Note) => {
    try {
      const updated = await notesApi.updateNote(note.id, {
        is_archived: !note.is_archived,
      });
      setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
    } catch {
      setError(`Failed to update archive status for "${note.title}".`);
    }
  };

  // Delete note
  const handleDeleteNote = async (note: Note) => {
    if (!window.confirm(`Are you sure you want to delete note "${note.title}"?`)) return;

    try {
      await notesApi.deleteNote(note.id);
      setNotes((prev) => prev.filter((n) => n.id !== note.id));
      if (selectedNoteId === note.id) {
        setSelectedNoteId(null);
        setEditorTitle('');
        setEditorContent('');
      }
    } catch {
      setError(`Failed to delete note "${note.title}".`);
    }
  };

  // Update metadata (associations)
  const handleUpdateMetadata = async (updates: {
    category_id?: string | null;
    project_id?: string | null;
    task_id?: string | null;
    tag_ids?: string[];
  }) => {
    if (!selectedNoteId) return;

    try {
      const updated = await notesApi.updateNote(selectedNoteId, updates);
      setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
    } catch {
      setError('Failed to update note associations.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
                DF
              </div>
              <span className="font-semibold text-lg tracking-tight text-white">DayFlow</span>
            </Link>

            <nav className="hidden sm:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/calendar"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Calendar</span>
              </Link>
              <Link
                to="/kanban"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <KanbanIcon className="w-3.5 h-3.5" />
                <span>Kanban</span>
              </Link>
              <Link
                to="/notes"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Notes</span>
              </Link>
              <Link
                to="/tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
              <Link
                to="/projects"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Folder className="w-3.5 h-3.5" />
                <span>Projects</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              className="px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-slate-300 hover:text-white text-xs font-medium transition flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col md:flex-row gap-6">
        {/* Error notification */}
        {error && (
          <div className="md:hidden mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {/* Left Column: Sidebar & Note List */}
        <div className="w-full md:w-80 lg:w-96 flex flex-col gap-4 shrink-0">
          <NoteSidebar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            selectedTag={selectedTag}
            onTagChange={setSelectedTag}
            filterView={filterView}
            onFilterViewChange={setFilterView}
            categories={categories}
            tags={tags}
            onNewNote={handleNewNote}
          />

          {/* Notes list */}
          <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-280px)] pr-1">
            {/* Pinned section */}
            {pinnedNotes.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 px-1">
                  <Pin className="w-3 h-3" />
                  <span>Pinned ({pinnedNotes.length})</span>
                </div>
                {pinnedNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    isSelected={selectedNoteId === note.id}
                    onSelect={handleSelectNote}
                    onTogglePin={handleTogglePin}
                    onToggleArchive={handleToggleArchive}
                    onDelete={handleDeleteNote}
                  />
                ))}
              </div>
            )}

            {/* Regular section */}
            <div className="space-y-2">
              {pinnedNotes.length > 0 && regularNotes.length > 0 && (
                <div className="text-xs font-semibold text-slate-400 px-1">Other Notes</div>
              )}
              {regularNotes.map((note) => (
                <NoteCard
                  key={note.id}
                  note={note}
                  isSelected={selectedNoteId === note.id}
                  onSelect={handleSelectNote}
                  onTogglePin={handleTogglePin}
                  onToggleArchive={handleToggleArchive}
                  onDelete={handleDeleteNote}
                />
              ))}
            </div>

            {/* Empty state */}
            {filteredNotes.length === 0 && !isLoading && (
              <div className="p-8 text-center rounded-2xl border-2 border-dashed border-slate-800 text-slate-500 text-xs">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <p className="font-semibold text-slate-400">No notes found</p>
                <p className="text-[11px] mt-0.5">Create a note or adjust your filters</p>
              </div>
            )}
          </div>
        </div>

        {/* Center & Right Column: Editor & Association Details */}
        <div className="flex-1 flex flex-col lg:flex-row gap-6 min-w-0">
          {selectedNoteId ? (
            <>
              {/* Note Editor */}
              <div className="flex-1 min-w-0 min-h-[500px]">
                <NoteEditor
                  title={editorTitle}
                  content={editorContent}
                  onTitleChange={handleTitleChange}
                  onContentChange={handleContentChange}
                  saveStatus={saveStatus}
                  lastSavedAt={lastSavedAt}
                  onSaveExplicit={handleSaveExplicit}
                />
              </div>

              {/* Note Metadata & Associations Panel */}
              {selectedNote && (
                <div className="w-full lg:w-72 shrink-0">
                  <NoteMetadataPanel
                    note={selectedNote}
                    projects={projects}
                    tasks={tasks}
                    categories={categories}
                    allTags={tags}
                    onUpdateMetadata={handleUpdateMetadata}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-slate-900/30 border border-slate-800 text-slate-500">
              <FileText className="w-12 h-12 text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-slate-300">No note selected</h3>
              <p className="text-xs text-slate-500 mt-1">
                Select a note from the left sidebar or create a new note to start writing.
              </p>
              <button
                onClick={handleNewNote}
                className="mt-4 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded-xl text-xs transition"
              >
                Create New Note
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
