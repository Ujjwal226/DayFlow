import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DashboardCustomizerModal } from '../components/dashboard/DashboardCustomizerModal';
import { DashboardWidgetConfig } from '../types/dashboard';

describe('DashboardCustomizerModal Component', () => {
  const initialWidgets: DashboardWidgetConfig[] = [
    { widget_id: 'welcome', is_visible: true, order: 0, size: 'full' },
    { widget_id: 'productivity_overview', is_visible: true, order: 1, size: 'full' },
    { widget_id: 'today_tasks', is_visible: true, order: 2, size: 'medium' },
  ];

  it('renders modal when isOpen is true', () => {
    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    expect(screen.getByText('Customize Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Welcome & Profile')).toBeInTheDocument();
    expect(screen.getByText('Productivity Overview')).toBeInTheDocument();
    expect(screen.getByText("Today's Tasks")).toBeInTheDocument();
  });

  it('toggles widget visibility', () => {
    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    // Initial state shows Visible button for Welcome & Profile
    const welcomeToggleBtn = screen.getByRole('button', { name: /Hide Welcome & Profile/i });
    expect(welcomeToggleBtn).toBeInTheDocument();

    fireEvent.click(welcomeToggleBtn);

    // Should now toggle to Show Welcome & Profile
    expect(screen.getByRole('button', { name: /Show Welcome & Profile/i })).toBeInTheDocument();
    expect(screen.getAllByText('Hidden').length).toBeGreaterThanOrEqual(1);
  });

  it('reorders widgets up and down', () => {
    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    const moveDownWelcomeBtn = screen.getByRole('button', { name: /Move Welcome & Profile Down/i });
    expect(moveDownWelcomeBtn).not.toBeDisabled();

    // First item move up button should be disabled
    const moveUpWelcomeBtn = screen.getByRole('button', { name: /Move Welcome & Profile Up/i });
    expect(moveUpWelcomeBtn).toBeDisabled();

    // Move welcome down
    fireEvent.click(moveDownWelcomeBtn);

    // Welcome move up button should now be enabled
    expect(screen.getByRole('button', { name: /Move Welcome & Profile Up/i })).not.toBeDisabled();
  });

  it('allows changing widget size', () => {
    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    // Find small button for today_tasks
    const smallBtns = screen.getAllByRole('button', { name: 'small' });
    // Click the third small button (today_tasks)
    fireEvent.click(smallBtns[2]);

    // Should receive active classes
    expect(smallBtns[2].className).toContain('bg-emerald-500/20');
  });

  it('calls onSave with normalized order on Save Layout click', async () => {
    const handleSave = vi.fn().mockResolvedValue(undefined);

    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={handleSave}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    const saveBtn = screen.getByRole('button', { name: /Save Layout/i });
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledTimes(1);
    const savedArg = handleSave.mock.calls[0][0];
    expect(savedArg).toHaveLength(3);
    expect(savedArg[0].order).toBe(0);
    expect(savedArg[1].order).toBe(1);
    expect(savedArg[2].order).toBe(2);
  });

  it('calls onReset on Restore Defaults click', () => {
    const handleReset = vi.fn().mockResolvedValue(undefined);

    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={vi.fn()}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={handleReset}
        isSaving={false}
        saveError={null}
      />
    );

    const resetBtn = screen.getByRole('button', { name: /Restore Defaults/i });
    fireEvent.click(resetBtn);

    expect(handleReset).toHaveBeenCalledTimes(1);
  });

  it('closes on Escape key press when not saving', () => {
    const handleClose = vi.fn();

    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={handleClose}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={false}
        saveError={null}
      />
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('does NOT close on Escape key press when saving is in progress', () => {
    const handleClose = vi.fn();

    render(
      <DashboardCustomizerModal
        isOpen={true}
        onClose={handleClose}
        currentWidgets={initialWidgets}
        onSave={vi.fn()}
        onReset={vi.fn()}
        isSaving={true}
        saveError={null}
      />
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).not.toHaveBeenCalled();
  });
});
