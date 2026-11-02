export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserRegisterRequest {
  email: string;
  display_name: string;
  password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface MessageResponse {
  status: string;
  message: string;
}

export interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (payload: UserRegisterRequest) => Promise<User>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}
