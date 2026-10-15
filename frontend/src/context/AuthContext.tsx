import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { User, UserLogin, UserRegister } from '../types/api';
import { authApi, clearAuthToken, getAuthToken, setAuthToken } from '../lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: UserLogin) => Promise<void>;
  register: (payload: UserRegister) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(async () => {
    try {
      if (getAuthToken()) {
        await authApi.logout();
      }
    } catch {
      // Ignore failure during logout
    } finally {
      clearAuthToken();
      setToken(null);
      setUser(null);
    }
  }, []);

  // Verify stored token on initial load
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = getAuthToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await authApi.me();
        setUser(currentUser);
        setToken(storedToken);
      } catch {
        clearAuthToken();
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    const handleUnauthorized = () => {
      setToken(null);
      setUser(null);
    };

    window.addEventListener('dayflow:auth_unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('dayflow:auth_unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (payload: UserLogin) => {
    const res = await authApi.login(payload);
    setAuthToken(res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const register = async (payload: UserRegister) => {
    const res = await authApi.register(payload);
    setAuthToken(res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
