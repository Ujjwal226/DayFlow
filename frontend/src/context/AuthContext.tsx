import React, { useCallback, useEffect, useState } from 'react';
import { authApi } from '../api/auth';
import { setAccessToken, setOnTokenExpired } from '../api/client';
import { AuthContext } from './auth-context';
import {
  User,
  UserLoginRequest,
  UserRegisterRequest,
} from '../types/auth';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const clearAuthState = useCallback(() => {
    setUser(null);
    setTokenState(null);
    setAccessToken(null);
  }, []);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const newToken = await authApi.refresh();
      if (!newToken) {
        clearAuthState();
        return false;
      }
      // Only set in-memory token temporarily, and ensure getMe succeeds before committing full auth state
      setAccessToken(newToken);
      try {
        const currentUser = await authApi.getMe();
        setTokenState(newToken);
        setUser(currentUser);
        return true;
      } catch {
        // If /me fails, invalidate the token and clear auth state to prevent inconsistent session
        clearAuthState();
        return false;
      }
    } catch {
      clearAuthState();
      return false;
    }
  }, [clearAuthState]);

  // Handle session initialization on initial mount
  useEffect(() => {
    let isMounted = true;
    setOnTokenExpired(() => {
      if (isMounted) {
        clearAuthState();
      }
    });

    const initAuth = async () => {
      setIsLoading(true);
      await refreshSession();
      if (isMounted) {
        setIsLoading(false);
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, [refreshSession, clearAuthState]);

  const login = async (credentials: UserLoginRequest): Promise<void> => {
    setIsLoading(true);
    try {
      const tokenData = await authApi.login(credentials);
      setTokenState(tokenData.access_token);
      const currentUser = await authApi.getMe();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: UserRegisterRequest): Promise<User> => {
    setIsLoading(true);
    try {
      return await authApi.register(payload);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } finally {
      clearAuthState();
      setIsLoading(false);
    }
  };

  const logoutAll = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logoutAll();
    } finally {
      clearAuthState();
      setIsLoading(false);
    }
  };

  const resendVerification = async (email: string): Promise<string> => {
    const res = await authApi.resendVerification({ email });
    return res.message;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoading,
        isAuthenticated: !!user && !!accessToken,
        login,
        register,
        logout,
        logoutAll,
        refreshSession,
        resendVerification,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

