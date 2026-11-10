import { apiClient } from './client';
import {
  Note,
  NoteCreatePayload,
  NoteFilterParams,
  NoteListResponse,
  NoteUpdatePayload,
} from '../types/note';
import { MessageResponse } from '../types/auth';

export const notesApi = {
  listNotes: async (params?: NoteFilterParams): Promise<NoteListResponse> => {
    const response = await apiClient.get<NoteListResponse>('/api/v1/notes', { params });
    return response.data;
  },

  getNote: async (noteId: string): Promise<Note> => {
    const response = await apiClient.get<Note>(`/api/v1/notes/${noteId}`);
    return response.data;
  },

  createNote: async (payload: NoteCreatePayload): Promise<Note> => {
    const response = await apiClient.post<Note>('/api/v1/notes', payload);
    return response.data;
  },

  updateNote: async (noteId: string, payload: NoteUpdatePayload): Promise<Note> => {
    const response = await apiClient.patch<Note>(`/api/v1/notes/${noteId}`, payload);
    return response.data;
  },

  deleteNote: async (noteId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/notes/${noteId}`);
    return response.data;
  },
};

