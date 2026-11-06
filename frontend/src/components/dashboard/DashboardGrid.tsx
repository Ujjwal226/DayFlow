import React from 'react';
import { DashboardWidgetConfig, WidgetSize } from '../../types/dashboard';
import { getWidgetDefinition } from './registry';
import { WidgetErrorBoundary } from './WidgetErrorBoundary';

interface DashboardGridProps {
  widgets: DashboardWidgetConfig[];
}

const getSizeClasses = (size: WidgetSize): string => {
  switch (size) {
    case 'small':
      return 'col-span-12 md:col-span-6 lg:col-span-4';
    case 'medium':
      return 'col-span-12 md:col-span-6 lg:col-span-6';
    case 'full':
    default:
      return 'col-span-12';
  }
};

export const DashboardGrid: React.FC<DashboardGridProps> = ({ widgets }) => {
  // Filter for only visible widgets and sort by order ascending
  const visibleWidgets = widgets
    .filter((w) => w.is_visible)
    .sort((a, b) => a.order - b.order);

  if (visibleWidgets.length === 0) {
    return (
      <div className="py-16 text-center text-slate-500 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
        <p className="text-sm font-medium text-slate-400">All dashboard widgets are currently hidden</p>
        <p className="text-xs text-slate-500 mt-1">
          Click "Customize Dashboard" above to configure your widget visibility.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-12 gap-5 sm:gap-6 auto-rows-max">
      {visibleWidgets.map((config) => {
        const definition = getWidgetDefinition(config.widget_id);
        if (!definition) {
          // Unknown widget fallback: ignore safely
          return null;
        }

        const Component = definition.component;
        const sizeClass = getSizeClasses(config.size);

        return (
          <div
            key={config.widget_id}
            data-widget-id={config.widget_id}
            className={`${sizeClass} flex flex-col`}
          >
            <WidgetErrorBoundary fallbackTitle={definition.title}>
              <Component widgetConfig={config} />
            </WidgetErrorBoundary>
          </div>
        );
      })}
    </div>
  );
};

