import React, { useState } from 'react';
import {
  Bold,
  Italic,
  Heading1,
  Heading2,
  List,
  ListOrdered,
  CheckSquare,
  Quote,
  Code,
  Link as LinkIcon,
  Eye,
  Edit3,
} from 'lucide-react';
import { MarkdownPreview } from './MarkdownPreview';

interface NoteEditorProps {
  title: string;
  content: string;
  onTitleChange: (newTitle: string) => void;
  onContentChange: (newContent: string) => void;
  saveStatus: 'saved' | 'saving' | 'unsaved' | 'error';
  lastSavedAt: Date | null;
  onSaveExplicit?: () => void;
}

export const NoteEditor: React.FC<NoteEditorProps> = ({
  title,
  content,
  onTitleChange,
  onContentChange,
  saveStatus,
  lastSavedAt,
  onSaveExplicit,
}) => {
  const [activeTab, setActiveTab] = useState<'edit' | 'preview' | 'split'>('split');
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const insertSnippet = (prefix: string, suffix: string = '', placeholder: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = content.substring(start, end) || placeholder;

    const replacement = `${prefix}${selected}${suffix}`;
    const newContent = content.substring(0, start) + replacement + content.substring(end);

    onContentChange(newContent);

    // Re-focus and set selection
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + prefix.length, start + prefix.length + selected.length);
    }, 0);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-2xl shadow-xl overflow-hidden backdrop-blur-md">
      {/* Editor Top Bar: Title, Save Status, Preview Tabs */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-900/90 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <input
          type="text"
          placeholder="Note title..."
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          className="flex-1 bg-transparent text-lg font-bold text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 rounded-lg px-2 py-1"
        />

        <div className="flex items-center gap-3 justify-between sm:justify-end">
          {/* Save Status Indicator */}
          <div className="text-xs flex items-center gap-1.5 font-medium">
            {saveStatus === 'saving' && (
              <span className="text-amber-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                Saving...
              </span>
            )}
            {saveStatus === 'saved' && (
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Saved{' '}
                {lastSavedAt && (
                  <span className="text-slate-500 hidden md:inline">
                    ({lastSavedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                  </span>
                )}
              </span>
            )}
            {saveStatus === 'unsaved' && (
              <span className="text-slate-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                Unsaved edits
              </span>
            )}
            {saveStatus === 'error' && (
              <span className="text-rose-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                Save failed
              </span>
            )}
          </div>

          {onSaveExplicit && saveStatus === 'unsaved' && (
            <button
              onClick={onSaveExplicit}
              className="px-2.5 py-1 bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-semibold rounded-lg shadow transition"
            >
              Save Now
            </button>
          )}

          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('edit')}
              className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 ${
                activeTab === 'edit'
                  ? 'bg-slate-800 text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Edit mode"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Edit</span>
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 ${
                activeTab === 'preview'
                  ? 'bg-slate-800 text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Preview mode"
            >
              <Eye className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('split')}
              className={`hidden lg:flex px-2.5 py-1 rounded-md transition items-center gap-1 ${
                activeTab === 'split'
                  ? 'bg-slate-800 text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Split view"
            >
              <span>Split</span>
            </button>
          </div>
        </div>
      </div>

      {/* Formatting Toolbar */}
      {activeTab !== 'preview' && (
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-1 flex-wrap text-slate-400">
          <button
            onClick={() => insertSnippet('**', '**', 'bold text')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Bold"
          >
            <Bold className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('*', '*', 'italic text')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Italic"
          >
            <Italic className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-slate-800 mx-1" />
          <button
            onClick={() => insertSnippet('# ', '', 'Heading 1')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Heading 1"
          >
            <Heading1 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('## ', '', 'Heading 2')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Heading 2"
          >
            <Heading2 className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-slate-800 mx-1" />
          <button
            onClick={() => insertSnippet('- ', '', 'List item')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Bulleted List"
          >
            <List className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('1. ', '', 'Numbered item')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Numbered List"
          >
            <ListOrdered className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('- [ ] ', '', 'Task item')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Checklist"
          >
            <CheckSquare className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-slate-800 mx-1" />
          <button
            onClick={() => insertSnippet('> ', '', 'Quote')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Blockquote"
          >
            <Quote className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('`', '`', 'code')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Inline Code"
          >
            <Code className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => insertSnippet('[', '](https://example.com)', 'link text')}
            className="p-1.5 hover:bg-slate-800 hover:text-slate-200 rounded transition"
            title="Link"
          >
            <LinkIcon className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Editor Body */}
      <div className="flex-1 flex overflow-hidden min-h-[400px]">
        {/* Raw Markdown Editor */}
        {(activeTab === 'edit' || activeTab === 'split') && (
          <div
            className={`flex-1 p-4 overflow-y-auto ${
              activeTab === 'split' ? 'border-r border-slate-800' : ''
            }`}
          >
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              placeholder="Write your note in Markdown here..."
              className="w-full h-full bg-transparent text-slate-200 font-mono text-sm leading-relaxed resize-none focus:outline-none placeholder-slate-600"
            />
          </div>
        )}

        {/* Rendered Preview */}
        {(activeTab === 'preview' || activeTab === 'split') && (
          <div className="flex-1 p-6 overflow-y-auto bg-slate-950/30">
            <MarkdownPreview content={content} />
          </div>
        )}
      </div>
    </div>
  );
};

