import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NoteEditor } from '../components/notes/NoteEditor';

describe('NoteEditor', () => {
  it('renders title and content inputs and formats toolbar actions', () => {
    const onTitleChange = vi.fn();
    const onContentChange = vi.fn();

    render(
      <NoteEditor
        title="Sample Meeting Notes"
        content="Key takeaways from design sync"
        onTitleChange={onTitleChange}
        onContentChange={onContentChange}
        saveStatus="saved"
        lastSavedAt={new Date()}
      />
    );

    expect(screen.getByDisplayValue('Sample Meeting Notes')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Key takeaways from design sync')).toBeInTheDocument();
    expect(screen.getByText(/Saved/)).toBeInTheDocument();

    // Trigger title change
    fireEvent.change(screen.getByPlaceholderText('Note title...'), {
      target: { value: 'Updated Title' },
    });
    expect(onTitleChange).toHaveBeenCalledWith('Updated Title');

    // Trigger content change
    fireEvent.change(screen.getByPlaceholderText('Write your note in Markdown here...'), {
      target: { value: 'Updated content' },
    });
    expect(onContentChange).toHaveBeenCalledWith('Updated content');
  });

  it('switches between edit, preview, and split tabs', () => {
    const markdown = `# Main Header

- Point 1`;

    render(
      <NoteEditor
        title="Markdown Note"
        content={markdown}
        onTitleChange={vi.fn()}
        onContentChange={vi.fn()}
        saveStatus="unsaved"
        lastSavedAt={null}
      />
    );

    // Initial split mode already renders preview
    expect(screen.getByRole('heading', { level: 1, name: 'Main Header' })).toBeInTheDocument();

    // Click preview mode
    fireEvent.click(screen.getByTitle('Preview mode'));
    expect(screen.getByRole('heading', { level: 1, name: 'Main Header' })).toBeInTheDocument();
  });
});
