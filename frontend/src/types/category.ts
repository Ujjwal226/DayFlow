export interface Category {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  color: string;
  icon: string | null;
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreatePayload {
  name: string;
  description?: string | null;
  color?: string;
  icon?: string | null;
}

export interface CategoryUpdatePayload {
  name?: string;
  description?: string | null;
  color?: string;
  icon?: string | null;
}

