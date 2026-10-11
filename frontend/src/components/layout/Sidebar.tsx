import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Sparkles,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../lib/utils';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  setIsCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'My Tasks', path: '/tasks', icon: CheckSquare },
    { name: 'Task History', path: '/history', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleNavClick = () => {
    if (mobileOpen) {
      setMobileOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          'fixed top-0 bottom-0 left-0 z-40 flex flex-col transition-all duration-300 ease-in-out',
          'bg-[var(--bg-surface)] border-r border-[var(--bg-border)] shadow-xl lg:shadow-none',
          // Desktop collapse width
          isCollapsed ? 'lg:w-20' : 'lg:w-64',
          // Mobile responsive slide-in
          mobileOpen ? 'translate-x-0 w-64' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center px-4 border-b border-[var(--bg-border)] justify-between">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-violet-500/20 shrink-0">
              <Sparkles className="w-5 h-5 text-white animate-pulse" />
            </div>
            {(!isCollapsed || mobileOpen) && (
              <div className="flex flex-col tracking-tight transition-opacity duration-200">
                <span className="font-bold text-lg text-[var(--text-primary)]">DayFlow</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-violet-400">Flow Your Day</span>
              </div>
            )}
          </div>

          {/* Desktop collapse button */}
          <button
            type="button"
            onClick={() => setIsCollapsed((prev) => !prev)}
            className="hidden lg:flex items-center justify-center p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={handleNavClick}
                className={({ isActive }) =>
                  cn(
                    'flex items-center px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 group relative',
                    isActive
                      ? 'bg-violet-600/15 text-violet-500 dark:text-violet-400 font-semibold'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]',
                    isCollapsed && !mobileOpen ? 'justify-center' : 'space-x-3'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={cn(
                        'w-5 h-5 shrink-0 transition-transform duration-200 group-hover:scale-110',
                        isActive ? 'text-violet-500 dark:text-violet-400' : 'text-[var(--text-secondary)]'
                      )}
                    />
                    {(!isCollapsed || mobileOpen) && (
                      <span className="truncate">{item.name}</span>
                    )}
                    {/* Active pill indicator */}
                    {isActive && (
                      <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-violet-600" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer controls: theme toggle & collapse hint */}
        <div className="p-3 border-t border-[var(--bg-border)] space-y-2">
          <button
            type="button"
            onClick={toggleTheme}
            className={cn(
              'w-full flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]',
              isCollapsed && !mobileOpen ? 'justify-center' : 'space-x-3'
            )}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-amber-400 shrink-0" />
            ) : (
              <Moon className="w-5 h-5 text-indigo-500 shrink-0" />
            )}
            {(!isCollapsed || mobileOpen) && (
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            )}
          </button>
        </div>
      </aside>
    </>
  );
};
