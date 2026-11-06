import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { DashboardWidgetConfig } from '../types/dashboard';

// Clean error log in tests for deliberate component throw
const originalError = console.error;

const CrashingWidget = () => {
  throw new Error('Exploding widget render failure');
};

const WorkingWidget = () => {
  return <div data-testid="working-widget">Working Content</div>;
};

vi.mock('../components/dashboard/registry', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../components/dashboard/registry')>();
  return {
    ...actual,
    getWidgetDefinition: (id: string) => {
      if (id === 'crash_widget') {
        return {
          id: 'crash_widget',
          title: 'Crashing Widget',
          description: 'A test widget that throws during render',
          defaultSize: 'medium',
          defaultVisible: true,
          supportedSizes: ['small', 'medium', 'full'],
          component: CrashingWidget,
        };
      }
      if (id === 'work_widget') {
        return {
          id: 'work_widget',
          title: 'Working Widget',
          description: 'A normal working widget',
          defaultSize: 'medium',
          defaultVisible: true,
          supportedSizes: ['small', 'medium', 'full'],
          component: WorkingWidget,
        };
      }
      return actual.getWidgetDefinition(id);
    },
  };
});

describe('Dashboard Widget Error Boundary & Isolation', () => {
  it('isolates a crashing widget so sibling widgets continue rendering', () => {
    console.error = vi.fn(); // suppress console error output during expected throw

    const widgets: DashboardWidgetConfig[] = [
      { widget_id: 'crash_widget', is_visible: true, order: 0, size: 'medium' },
      { widget_id: 'work_widget', is_visible: true, order: 1, size: 'medium' },
    ];

    render(<DashboardGrid widgets={widgets} />);

    // Working widget renders normally
    expect(screen.getByTestId('working-widget')).toBeInTheDocument();

    // Crashing widget renders localized fallback error card
    expect(screen.getByText('Crashing Widget')).toBeInTheDocument();
    expect(
      screen.getByText('An unexpected error occurred while rendering this widget.')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();

    console.error = originalError;
  });
});
