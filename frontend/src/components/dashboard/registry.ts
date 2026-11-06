import {
  DashboardWidgetId,
  WidgetDefinition,
  WidgetSize,
} from '../../types/dashboard';
import { WelcomeWidget } from './widgets/WelcomeWidget';
import { TodayTasksWidget } from './widgets/TodayTasksWidget';
import { UpcomingTasksWidget } from './widgets/UpcomingTasksWidget';
import { OverdueTasksWidget } from './widgets/OverdueTasksWidget';
import { ProductivityOverviewWidget } from './widgets/ProductivityOverviewWidget';
import { RecentActivityWidget } from './widgets/RecentActivityWidget';
import { ProjectsOverviewWidget } from './widgets/ProjectsOverviewWidget';
import { ProductivityTrendsWidget } from './widgets/ProductivityTrendsWidget';
import { RecurringInsightsWidget } from './widgets/RecurringInsightsWidget';
import { QuickActionsWidget } from './widgets/QuickActionsWidget';

const ALL_SIZES: WidgetSize[] = ['small', 'medium', 'full'];

export const WIDGET_REGISTRY: Record<DashboardWidgetId, WidgetDefinition> = {
  welcome: {
    id: 'welcome',
    title: 'Welcome & Profile',
    description: 'User profile, session information, and verification status',
    defaultSize: 'full',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: WelcomeWidget,
  },
  productivity_overview: {
    id: 'productivity_overview',
    title: 'Productivity Overview',
    description: 'Summary KPIs of completion rate, active tasks, and velocity',
    defaultSize: 'full',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: ProductivityOverviewWidget,
  },
  today_tasks: {
    id: 'today_tasks',
    title: "Today's Tasks",
    description: 'High-priority tasks due today',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: TodayTasksWidget,
  },
  upcoming_tasks: {
    id: 'upcoming_tasks',
    title: 'Upcoming Tasks',
    description: 'Tasks scheduled for the next 7 days',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: UpcomingTasksWidget,
  },
  overdue_tasks: {
    id: 'overdue_tasks',
    title: 'Overdue Tasks',
    description: 'Urgent incomplete items past their due dates',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: OverdueTasksWidget,
  },
  recent_activity: {
    id: 'recent_activity',
    title: 'Recent Activity',
    description: 'Chronological timeline of task and project actions',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: RecentActivityWidget,
  },
  projects_overview: {
    id: 'projects_overview',
    title: 'Projects Overview',
    description: 'Progress of ongoing projects and initiatives',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: ProjectsOverviewWidget,
  },
  productivity_trends: {
    id: 'productivity_trends',
    title: 'Productivity Trends',
    description: 'Daily completion trends over the past 7 days',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: ProductivityTrendsWidget,
  },
  recurring_insights: {
    id: 'recurring_insights',
    title: 'Recurring Tasks',
    description: 'Active recurring series and upcoming occurrences',
    defaultSize: 'medium',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: RecurringInsightsWidget,
  },
  quick_actions: {
    id: 'quick_actions',
    title: 'Quick Actions',
    description: 'Rapid shortcuts to create tasks, projects, or view insights',
    defaultSize: 'full',
    defaultVisible: true,
    supportedSizes: ALL_SIZES,
    component: QuickActionsWidget,
  },
};

export const getWidgetDefinition = (
  id: string
): WidgetDefinition | undefined => {
  return WIDGET_REGISTRY[id as DashboardWidgetId];
};

