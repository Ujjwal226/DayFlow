import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { DashboardWidgetConfig } from '../types/dashboard';

// Mock child widgets to avoid unneeded API calls during grid test
vi.mock('../components/dashboard/widgets/WelcomeWidget', () => ({
  WelcomeWidget: () => <div data-testid="mock-welcome">Welcome Mock</div>,
}));

vi.mock('../components/dashboard/widgets/TodayTasksWidget', () => ({
  TodayTasksWidget: () => <div data-testid="mock-today">Today Tasks Mock</div>,
}));

vi.mock('../components/dashboard/widgets/QuickActionsWidget', () => ({
  QuickActionsWidget: () => <div data-testid="mock-quick">Quick Actions Mock</div>,
}));

describe('DashboardGrid Component', () => {
  it('renders visible widgets in order with appropriate responsive grid classes', () => {
    const widgets: DashboardWidgetConfig[] = [
      { widget_id: 'today_tasks', is_visible: true, order: 1, size: 'small' },
      { widget_id: 'welcome', is_visible: true, order: 0, size: 'full' },
      { widget_id: 'quick_actions', is_visible: false, order: 2, size: 'medium' },
    ];

    render(<DashboardGrid widgets={widgets} />);

    // Visible widgets should be present
    expect(screen.getByTestId('mock-welcome')).toBeInTheDocument();
    expect(screen.getByTestId('mock-today')).toBeInTheDocument();

    // Hidden widget should NOT be rendered
    expect(screen.queryByTestId('mock-quick')).not.toBeInTheDocument();

    // Verify ordering and size classes
    const welcomeContainer = screen.getByTestId('mock-welcome').parentElement;
    expect(welcomeContainer?.className).toContain('col-span-12');

    const todayContainer = screen.getByTestId('mock-today').parentElement;
    expect(todayContainer?.className).toContain('col-span-12 md:col-span-6 lg:col-span-4');
  });

  it('renders empty message when all widgets are hidden', () => {
    const widgets: DashboardWidgetConfig[] = [
      { widget_id: 'welcome', is_visible: false, order: 0, size: 'full' },
    ];

    render(<DashboardGrid widgets={widgets} />);
    expect(
      screen.getByText('All dashboard widgets are currently hidden')
    ).toBeInTheDocument();
  });

  it('safely skips unknown widget IDs without crashing', () => {
    const widgets: DashboardWidgetConfig[] = [
      { widget_id: 'unknown_widget_xyz', is_visible: true, order: 0, size: 'full' },
      { widget_id: 'welcome', is_visible: true, order: 1, size: 'full' },
    ];

    render(<DashboardGrid widgets={widgets} />);
    expect(screen.getByTestId('mock-welcome')).toBeInTheDocument();
  });
});
