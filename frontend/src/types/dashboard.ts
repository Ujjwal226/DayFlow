import React from 'react';

export type WidgetSize = 'small' | 'medium' | 'full';

export type DashboardWidgetId =
  | 'welcome'
  | 'today_tasks'
  | 'upcoming_tasks'
  | 'overdue_tasks'
  | 'productivity_overview'
  | 'recent_activity'
  | 'projects_overview'
  | 'productivity_trends'
  | 'recurring_insights'
  | 'quick_actions'
  | 'active_goals'
  | 'upcoming_goal_deadlines'
  | 'goal_progress_overview'
  | 'recently_completed_goals'
  | 'at_risk_goals'
  | 'finance_net_worth'
  | 'finance_cash_flow';

export interface DashboardWidgetConfig {
  widget_id: DashboardWidgetId | string;
  is_visible: boolean;
  order: number;
  size: WidgetSize;
}

export interface DashboardLayoutResponse {
  id: string | null;
  user_id: string | null;
  widgets: DashboardWidgetConfig[];
  is_customized: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface DashboardLayoutUpdateRequest {
  widgets: DashboardWidgetConfig[];
}

export interface WidgetProps {
  widgetConfig: DashboardWidgetConfig;
}

export interface WidgetDefinition {
  id: DashboardWidgetId;
  title: string;
  description: string;
  defaultSize: WidgetSize;
  defaultVisible: boolean;
  supportedSizes: WidgetSize[];
  component: React.ComponentType<WidgetProps>;
}

