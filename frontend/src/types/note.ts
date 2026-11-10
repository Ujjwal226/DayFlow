import { Category } from './category';
import { Tag } from './tag';

export interface NoteProjectReference {
  id: string;
  name: string;
  color?: string | null;
}

export interface NoteTaskReference {
  id: string;
  title: string;
  status: string;
  priority: string;
}

export interface Note {
  id: string;
  user_id: string;
  title: string;
  content: string;
  is_pinned: boolean;
  is_archived: boolean;
  category_id?: string | null;
  category?: Category | null;
  project_id?: string | null;
  project?: NoteProjectReference | null;
  task_id?: string | null;
  task?: NoteTaskReference | null;
  tags?: Tag[];
  created_at: string;
  updated_at: string;
}

export interface NoteCreatePayload {
  title: string;
  content?: string;
  is_pinned?: boolean;
  category_id?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  tag_ids?: string[];
}

export interface NoteUpdatePayload {
  title?: string;
  content?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
  category_id?: string | null;
  project_id?: string | null;
  task_id?: string | null;
  tag_ids?: string[];
}

export interface NoteListResponse {
  items: Note[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface NoteFilterParams {
  page?: number;
  page_size?: number;
  search?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
  category_id?: string;
  project_id?: string;
  task_id?: string;
  tag_id?: string;
}

