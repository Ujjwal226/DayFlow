import React from 'react';
import { AuthLayout } from '../layouts/AuthLayout';
import { RegisterForm } from '../components/auth/RegisterForm';

export const RegisterPage: React.FC = () => {
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start your productivity and finance journey with DayFlow"
    >
      <RegisterForm />
    </AuthLayout>
  );
};

