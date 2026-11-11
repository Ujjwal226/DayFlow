import { describe, it, expect } from 'vitest';
import { WIDGET_REGISTRY, getWidgetDefinition } from '../components/dashboard/registry';
import { DashboardWidgetId } from '../types/dashboard';

describe('Widget Registry', () => {
  const expectedWidgetIds: DashboardWidgetId[] = [
    'welcome',
    'productivity_overview',
    'today_tasks',
    'upcoming_tasks',
    'overdue_tasks',
    'recent_activity',
    'projects_overview',
    'productivity_trends',
    'recurring_insights',
    'quick_actions',
    'active_goals',
    'upcoming_goal_deadlines',
    'goal_progress_overview',
    'recently_completed_goals',
    'at_risk_goals',
  ];

  it('registers all fifteen expected widgets', () => {
    const registeredIds = Object.keys(WIDGET_REGISTRY);
    expect(registeredIds).toHaveLength(15);
    for (const expectedId of expectedWidgetIds) {
      expect(registeredIds).toContain(expectedId);
    }
  });

  it('provides valid components and metadata for every registered widget', () => {
    for (const id of expectedWidgetIds) {
      const def = getWidgetDefinition(id);
      expect(def).toBeDefined();
      expect(def?.id).toBe(id);
      expect(def?.title).toBeTruthy();
      expect(def?.description).toBeTruthy();
      expect(def?.component).toBeDefined();
      expect(['small', 'medium', 'full']).toContain(def?.defaultSize);
      expect(typeof def?.defaultVisible).toBe('boolean');
      expect(def?.supportedSizes).toEqual(['small', 'medium', 'full']);
    }
  });

  it('safely handles unknown widget IDs without crashing', () => {
    const unknown = getWidgetDefinition('unknown_widget_xyz');
    expect(unknown).toBeUndefined();
  });
});

