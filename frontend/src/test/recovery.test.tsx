import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { ResetPasswordPage } from '../pages/ResetPasswordPage';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import { authApi } from '../api/auth';

vi.mock('../api/auth', () => ({
  authApi: {
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
  },
}));

describe('Email Verification & Password Recovery Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ForgotPasswordPage', () => {
    it('validates empty email and submits valid email', async () => {
      vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({
        status: 'ok',
        message: 'If an account exists with this email address, password reset instructions have been sent.',
      });

      render(
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      );

      const submitBtn = screen.getByRole('button', { name: /send reset instructions/i });
      await userEvent.click(submitBtn);

      expect(await screen.findByText(/email address is required/i)).toBeInTheDocument();
      expect(authApi.forgotPassword).not.toHaveBeenCalled();

      const emailInput = screen.getByLabelText(/account email/i);
      await userEvent.type(emailInput, 'user@example.com');
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(authApi.forgotPassword).toHaveBeenCalledWith({ email: 'user@example.com' });
        expect(screen.getByText(/instructions have been sent/i)).toBeInTheDocument();
      });
    });
  });

  describe('ResetPasswordPage', () => {
    it('displays error if token is missing from query string', () => {
      render(
        <MemoryRouter initialEntries={['/reset-password']}>
          <Routes>
            <Route path="/reset-password" element={<ResetPasswordPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText(/invalid or missing reset token link/i)).toBeInTheDocument();
    });

    it('validates matching passwords and submits reset', async () => {
      vi.mocked(authApi.resetPassword).mockResolvedValueOnce({
        status: 'ok',
        message: 'Your password has been reset successfully.',
      });

      render(
        <MemoryRouter initialEntries={['/reset-password?token=valid-secret-token']}>
          <Routes>
            <Route path="/reset-password" element={<ResetPasswordPage />} />
          </Routes>
        </MemoryRouter>
      );

      const passwordInput = screen.getByLabelText(/^new password/i);
      const confirmInput = screen.getByLabelText(/^confirm new password/i);
      const submitBtn = screen.getByRole('button', { name: /reset password/i });

      await userEvent.type(passwordInput, 'NewPass123!');
      await userEvent.type(confirmInput, 'Mismatch123!');
      await userEvent.click(submitBtn);

      expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
      expect(authApi.resetPassword).not.toHaveBeenCalled();

      await userEvent.clear(confirmInput);
      await userEvent.type(confirmInput, 'NewPass123!');
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(authApi.resetPassword).toHaveBeenCalledWith({
          token: 'valid-secret-token',
          new_password: 'NewPass123!',
        });
      });
    });
  });

  describe('VerifyEmailPage', () => {
    it('verifies email successfully with valid token', async () => {
      vi.mocked(authApi.verifyEmail).mockResolvedValueOnce({
        status: 'ok',
        message: 'Email address verified successfully.',
      });

      render(
        <MemoryRouter initialEntries={['/verify-email?token=valid-verification-token']}>
          <Routes>
            <Route path="/verify-email" element={<VerifyEmailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(authApi.verifyEmail).toHaveBeenCalledWith({ token: 'valid-verification-token' });
        expect(screen.getByText('Email Verified!')).toBeInTheDocument();
        expect(screen.getByText(/Email address verified successfully/i)).toBeInTheDocument();
      });
    });

    it('shows failure when verification fails', async () => {
      vi.mocked(authApi.verifyEmail).mockRejectedValueOnce(
        new Error('This verification link has expired.')
      );

      render(
        <MemoryRouter initialEntries={['/verify-email?token=expired-token']}>
          <Routes>
            <Route path="/verify-email" element={<VerifyEmailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText(/This verification link has expired/i)).toBeInTheDocument();
      });
    });
  });
});

