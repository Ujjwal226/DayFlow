import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { useAuth } from '../hooks/useAuth';
import { ProtectedRoute, PublicOnlyRoute } from '../routes/ProtectedRoute';
import { authApi } from '../api/auth';
import { getAccessToken } from '../api/client';

vi.mock('../api/auth', () => ({
  authApi: {
    refresh: vi.fn(),
    getMe: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    logoutAll: vi.fn(),
  },
}));

const TestDashboard: React.FC = () => {
  const { user, logout, logoutAll } = useAuth();
  return (
    <div>
      <h1>Protected Dashboard</h1>
      <p>Hello, {user?.display_name}</p>
      <button onClick={() => logout()}>Sign Out</button>
      <button onClick={() => logoutAll()}>Sign Out All</button>
    </div>
  );
};

const TestLogin: React.FC = () => {
  return <h1>Public Login Page</h1>;
};

describe('Session Restoration, Protection & Logout Flows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('restores authenticated session when valid refresh cookie exists', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce('valid-session-jwt');
    vi.mocked(authApi.getMe).mockResolvedValueOnce({
      id: 'user-uuid-1',
      email: 'member@example.com',
      display_name: 'Member Jane',
      is_active: true,
      is_verified: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="/login" element={<TestLogin />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TestDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    // Initial state renders the verifying spinner
    expect(screen.getByText(/verifying secure session/i)).toBeInTheDocument();

    // After resolution, dashboard renders
    await waitFor(() => {
      expect(screen.getByText('Protected Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/Hello, Member Jane/i)).toBeInTheDocument();
    });

    expect(getAccessToken()).toBe('valid-session-jwt');
  });

  it('redirects to login when session restoration fails (no cookie or 401)', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce(null);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="/login" element={<TestLogin />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TestDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Public Login Page')).toBeInTheDocument();
    });
    expect(screen.queryByText('Protected Dashboard')).not.toBeInTheDocument();
  });

  it('cleans up in-memory token and denies access if getMe fails after refresh', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce('temporary-token');
    vi.mocked(authApi.getMe).mockRejectedValueOnce(new Error('User inactive or deleted'));

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="/login" element={<TestLogin />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TestDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Public Login Page')).toBeInTheDocument();
    });
    expect(getAccessToken()).toBeNull();
  });

  it('redirects authenticated users away from public-only pages (/login)', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce('valid-session-jwt');
    vi.mocked(authApi.getMe).mockResolvedValueOnce({
      id: 'user-uuid-1',
      email: 'member@example.com',
      display_name: 'Member Jane',
      is_active: true,
      is_verified: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route
              path="/login"
              element={
                <PublicOnlyRoute>
                  <TestLogin />
                </PublicOnlyRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TestDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Dashboard')).toBeInTheDocument();
    });
    expect(screen.queryByText('Public Login Page')).not.toBeInTheDocument();
  });

  it('clears state and redirects on logout', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce('valid-session-jwt');
    vi.mocked(authApi.getMe).mockResolvedValueOnce({
      id: 'user-uuid-1',
      email: 'member@example.com',
      display_name: 'Member Jane',
      is_active: true,
      is_verified: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });
    vi.mocked(authApi.logout).mockResolvedValueOnce({ status: 'ok', message: 'Logged out' });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="/login" element={<TestLogin />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <TestDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Dashboard')).toBeInTheDocument();
    });

    const logoutBtn = screen.getByRole('button', { name: /sign out$/i });
    logoutBtn.click();

    await waitFor(() => {
      expect(authApi.logout).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Public Login Page')).toBeInTheDocument();
    });

    expect(getAccessToken()).toBeNull();
  });
});

