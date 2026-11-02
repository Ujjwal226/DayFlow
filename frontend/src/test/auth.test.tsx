import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';
import { AuthContext } from '../context/auth-context';
import { AuthContextType } from '../types/auth';

const mockAuthContext: AuthContextType = {
  user: null,
  accessToken: null,
  isLoading: false,
  isAuthenticated: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  logoutAll: vi.fn(),
  refreshSession: vi.fn(),
  resendVerification: vi.fn(),
};

describe('Authentication Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('LoginForm', () => {
    it('renders email and password inputs and submits with valid data', async () => {
      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter>
            <LoginForm />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const submitBtn = screen.getByRole('button', { name: /sign in/i });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(passwordInput, 'ValidPassword123!');
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(mockAuthContext.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'ValidPassword123!',
        });
      });
    });

    it('toggles password visibility', async () => {
      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter>
            <LoginForm />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      const passwordInput = screen.getByLabelText(/^password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');

      const toggleBtn = screen.getByLabelText(/show password/i);
      await userEvent.click(toggleBtn);

      expect(passwordInput).toHaveAttribute('type', 'text');
    });

    it('validates empty inputs on submit', async () => {
      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter>
            <LoginForm />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      const submitBtn = screen.getByRole('button', { name: /sign in/i });
      await userEvent.click(submitBtn);

      expect(await screen.findByText(/email address is required/i)).toBeInTheDocument();
      expect(mockAuthContext.login).not.toHaveBeenCalled();
    });
  });

  describe('RegisterForm', () => {
    it('validates password requirements and matching passwords', async () => {
      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter>
            <RegisterForm />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      const nameInput = screen.getByLabelText(/full name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmInput = screen.getByLabelText(/^confirm password/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      await userEvent.type(nameInput, 'Alex Morgan');
      await userEvent.type(emailInput, 'alex@example.com');
      await userEvent.type(passwordInput, 'weak');
      await userEvent.type(confirmInput, 'mismatch');
      await userEvent.click(submitBtn);

      expect(
        await screen.findByText(/password does not satisfy requirements/i)
      ).toBeInTheDocument();
      expect(mockAuthContext.register).not.toHaveBeenCalled();
    });

    it('submits registration when all fields are valid', async () => {
      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter>
            <RegisterForm />
          </MemoryRouter>
        </AuthContext.Provider>
      );

      const nameInput = screen.getByLabelText(/full name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmInput = screen.getByLabelText(/^confirm password/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      await userEvent.type(nameInput, 'Alex Morgan');
      await userEvent.type(emailInput, 'alex@example.com');
      await userEvent.type(passwordInput, 'ValidPassword123!');
      await userEvent.type(confirmInput, 'ValidPassword123!');
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(mockAuthContext.register).toHaveBeenCalledWith({
          display_name: 'Alex Morgan',
          email: 'alex@example.com',
          password: 'ValidPassword123!',
        });
      });
    });
  });
});

