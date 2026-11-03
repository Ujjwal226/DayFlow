export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color: string | null;
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface TagCreatePayload {
  name: string;
  color?: string | null;
}

export interface TagUpdatePayload {
  name?: string;
  color?: string | null;
}

