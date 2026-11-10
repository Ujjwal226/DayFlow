import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { NotesPage } from '../pages/NotesPage';
import { notesApi } from '../api/notes';
import { projectsApi } from '../api/projects';
import { tasksApi } from '../api/tasks';
import { categoriesApi } from '../api/categories';
import { tagsApi } from '../api/tags';

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@dayflow.com', full_name: 'Test User' },
    logout: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock('../api/notes', () => ({
  notesApi: {
    listNotes: vi.fn(),
    createNote: vi.fn(),
    updateNote: vi.fn(),
    deleteNote: vi.fn(),
  },
}));

vi.mock('../api/projects', () => ({
  projectsApi: {
    list: vi.fn(),
  },
}));

vi.mock('../api/tasks', () => ({
  tasksApi: {
    listTasks: vi.fn(),
  },
}));

vi.mock('../api/categories', () => ({
  categoriesApi: {
    listCategories: vi.fn(),
  },
}));

vi.mock('../api/tags', () => ({
  tagsApi: {
    listTags: vi.fn(),
  },
}));

describe('NotesPage', () => {
  const mockNotes = [
    {
      id: 'note-1',
      user_id: 'user-1',
      title: 'Sprint Planning Notes',
      content: 'Discussion regarding Sprint 12 deliverables',
      is_pinned: true,
      is_archived: false,
      category_id: null,
      project_id: null,
      task_id: null,
      tags: [],
      created_at: '2026-11-10T00:00:00Z',
      updated_at: '2026-11-10T00:00:00Z',
    },
    {
      id: 'note-2',
      user_id: 'user-1',
      title: 'DevOps Checklist',
      content: 'Docker, CI/CD, and DB migrations',
      is_pinned: false,
      is_archived: false,
      category_id: null,
      project_id: null,
      task_id: null,
      tags: [],
      created_at: '2026-11-11T00:00:00Z',
      updated_at: '2026-11-11T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (notesApi.listNotes as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: mockNotes,
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (projectsApi.list as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (tasksApi.listTasks as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (categoriesApi.listCategories as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tagsApi.listTags as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });

  it('renders notes list with pinned notes and loads editor', async () => {
    render(
      <MemoryRouter>
        <NotesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sprint Planning Notes')).toBeInTheDocument();
      expect(screen.getByText('DevOps Checklist')).toBeInTheDocument();
      expect(screen.getByText(/Pinned/)).toBeInTheDocument();
    });

    // Verify first note loaded into editor
    expect(screen.getByDisplayValue('Sprint Planning Notes')).toBeInTheDocument();
  });

  it('creates a new note when clicking New Note', async () => {
    (notesApi.createNote as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      id: 'note-new',
      user_id: 'user-1',
      title: 'Untitled Note',
      content: '',
      is_pinned: false,
      is_archived: false,
      category_id: null,
      project_id: null,
      task_id: null,
      tags: [],
      created_at: '2026-11-11T12:00:00Z',
      updated_at: '2026-11-11T12:00:00Z',
    });

    render(
      <MemoryRouter>
        <NotesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sprint Planning Notes')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('New Note'));

    await waitFor(() => {
      expect(notesApi.createNote).toHaveBeenCalledWith({
        title: 'Untitled Note',
        content: '',
        is_pinned: false,
      });
    });
  });

  it('toggles pinned state on a note', async () => {
    (notesApi.updateNote as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockNotes[0],
      is_pinned: false,
    });

    render(
      <MemoryRouter>
        <NotesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sprint Planning Notes')).toBeInTheDocument();
    });

    const unpinButtons = screen.getAllByTitle('Unpin note');
    fireEvent.click(unpinButtons[0]);

    await waitFor(() => {
      expect(notesApi.updateNote).toHaveBeenCalledWith('note-1', { is_pinned: false });
    });
  });
});

