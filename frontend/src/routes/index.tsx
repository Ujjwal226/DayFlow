import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { WelcomePage } from '../pages/WelcomePage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="*" element={<WelcomePage />} />
    </Routes>
  );
};

