import React from 'react';
import { AuthLayout } from '../layouts/AuthLayout';
import { LoginForm } from '../components/auth/LoginForm';

export const LoginPage: React.FC = () => {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your DayFlow account to continue"
    >
      <LoginForm />
    </AuthLayout>
  );
};

