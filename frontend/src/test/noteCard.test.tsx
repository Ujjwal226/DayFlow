import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NoteCard } from '../components/notes/NoteCard';
import { Note } from '../types/note';

describe('NoteCard', () => {
  const mockNote: Note = {
    id: 'note-1',
    user_id: 'user-1',
    title: 'Product Roadmap Q1',
    content: 'Deliver Notes and Knowledge management',
    is_pinned: false,
    is_archived: false,
    category: {
      id: 'cat-1',
      user_id: 'user-1',
      name: 'Strategy',
      description: null,
      color: '#10B981',
      icon: null,
      task_count: 0,
      created_at: '',
      updated_at: '',
    },
    project: {
      id: 'proj-1',
      name: 'DayFlow v2',
    },
    task: {
      id: 'task-1',
      title: 'Setup Notes UI',
      status: 'TODO',
      priority: 'HIGH',
    },
    tags: [
      { id: 'tag-1', user_id: 'user-1', name: 'roadmap', color: '#10B981', task_count: 0, created_at: '', updated_at: '' },
    ],
    created_at: '2026-11-10T10:00:00Z',
    updated_at: '2026-11-11T12:00:00Z',
  };

  it('renders note details, associations, and category badge', () => {
    render(
      <NoteCard
        note={mockNote}
        isSelected={false}
        onSelect={vi.fn()}
        onTogglePin={vi.fn()}
        onToggleArchive={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('Product Roadmap Q1')).toBeInTheDocument();
    expect(screen.getByText(/Deliver Notes and Knowledge management/)).toBeInTheDocument();
    expect(screen.getByText('Strategy')).toBeInTheDocument();
    expect(screen.getByText('DayFlow v2')).toBeInTheDocument();
    expect(screen.getByText('Setup Notes UI')).toBeInTheDocument();
    expect(screen.getByText('#roadmap')).toBeInTheDocument();
  });

  it('handles click actions for select, pin, archive, and delete', () => {
    const onSelect = vi.fn();
    const onTogglePin = vi.fn();
    const onToggleArchive = vi.fn();
    const onDelete = vi.fn();

    render(
      <NoteCard
        note={mockNote}
        isSelected={false}
        onSelect={onSelect}
        onTogglePin={onTogglePin}
        onToggleArchive={onToggleArchive}
        onDelete={onDelete}
      />
    );

    fireEvent.click(screen.getByText('Product Roadmap Q1'));
    expect(onSelect).toHaveBeenCalledWith(mockNote);

    fireEvent.click(screen.getByTitle('Pin note'));
    expect(onTogglePin).toHaveBeenCalledWith(mockNote);

    fireEvent.click(screen.getByTitle('Archive note'));
    expect(onToggleArchive).toHaveBeenCalledWith(mockNote);

    fireEvent.click(screen.getByTitle('Delete note'));
    expect(onDelete).toHaveBeenCalledWith(mockNote);
  });
});

