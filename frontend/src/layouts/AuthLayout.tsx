import React from 'react';
import { Link } from 'react-router-dom';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ title, subtitle, children }) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-emerald-500 selection:text-white relative overflow-hidden">
      {/* Decorative ambient background glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[35rem] h-[35rem] bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10">
        <Link to="/" className="flex items-center justify-center gap-3 group mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition transform">
            DF
          </div>
          <span className="font-bold text-2xl tracking-tight text-white group-hover:text-emerald-400 transition">
            DayFlow
          </span>
        </Link>
        <h2 className="text-center text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          {title}
        </h2>
        <p className="mt-2 text-center text-sm text-slate-400">
          {subtitle}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0 z-10">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
          {children}
        </div>
      </div>

      <footer className="mt-8 text-center text-xs text-slate-600">
        DayFlow &copy; 2026 • Secure Multi-User Productivity & Finance
      </footer>
    </div>
  );
};

