import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { calendarApi } from '../api/calendar';
import {
  CalendarEventCreatePayload,
  CalendarEventItem,
  CalendarEventUpdatePayload,
  CalendarFeedItem,
  CalendarViewMode,
  ScheduleTaskPayload,
} from '../types/calendar';
import { CalendarToolbar } from '../components/calendar/CalendarToolbar';
import { MonthView } from '../components/calendar/MonthView';
import { WeekView } from '../components/calendar/WeekView';
import { DayView } from '../components/calendar/DayView';
import { CalendarEventModal } from '../components/calendar/CalendarEventModal';
import { TaskSchedulingModal } from '../components/calendar/TaskSchedulingModal';
import { CalendarFilterDrawer, CalendarFilterState } from '../components/calendar/CalendarFilterDrawer';
import {
  Calendar as CalendarIcon,
  Layers,
  CheckSquare,
  LogOut,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

export const CalendarPage: React.FC = () => {
  const { logout, logoutAll, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<CalendarViewMode>('month');

  const [items, setItems] = useState<CalendarFeedItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEventItem | null>(null);
  const [prefillDate, setPrefillDate] = useState<Date | null>(null);

  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);

  // Filters state
  const [filters, setFilters] = useState<CalendarFilterState>({
    includeTasks: true,
    includeEvents: true,
    projectId: null,
    categoryId: null,
    status: null,
    priority: null,
    recurringOnly: false,
  });

  // Calculate count of active filters (excluding default inclusions)
  const activeFilterCount =
    (filters.projectId ? 1 : 0) +
    (filters.categoryId ? 1 : 0) +
    (filters.status ? 1 : 0) +
    (filters.priority ? 1 : 0) +
    (filters.recurringOnly ? 1 : 0) +
    (!filters.includeTasks ? 1 : 0) +
    (!filters.includeEvents ? 1 : 0);

  // Request race-condition counter
  const requestIdRef = useRef<number>(0);

  // Derive visible range from current date and view mode
  const calculateVisibleRange = useCallback((): { start: Date; end: Date } => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    if (viewMode === 'month') {
      const start = new Date(year, month, 1, 0, 0, 0);
      const day = start.getDay();
      const diff = (day === 0 ? -6 : 1) - day;
      start.setDate(start.getDate() + (diff > 0 ? diff - 7 : diff));

      const end = new Date(start);
      end.setDate(start.getDate() + 42); // 6 weeks * 7 days
      return { start, end };
    }

    if (viewMode === 'week') {
      const d = new Date(currentDate);
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const start = new Date(d.getFullYear(), d.getMonth(), diff, 0, 0, 0);
      const end = new Date(start);
      end.setDate(start.getDate() + 7);
      return { start, end };
    }

    // Day view
    const start = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 0, 0, 0);
    const end = new Date(start);
    end.setDate(start.getDate() + 1);
    return { start, end };
  }, [currentDate, viewMode]);

  const fetchFeed = useCallback(async () => {
    const currentReqId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);

    const { start, end } = calculateVisibleRange();
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

    try {
      const response = await calendarApi.getFeed({
        start: start.toISOString(),
        end: end.toISOString(),
        timezone: tz,
        include_tasks: filters.includeTasks,
        include_events: filters.includeEvents,
        project_id: filters.projectId || undefined,
        category_id: filters.categoryId || undefined,
        status: filters.status || undefined,
        priority: filters.priority || undefined,
        recurring_only: filters.recurringOnly ? true : undefined,
      });

      if (currentReqId === requestIdRef.current) {
        setItems(response.items);
      }
    } catch {
      if (currentReqId === requestIdRef.current) {
        setError('Failed to load calendar feed. Please try again.');
      }
    } finally {
      if (currentReqId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  }, [calculateVisibleRange, filters]);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  // Period navigation
  const handlePrev = () => {
    const next = new Date(currentDate);
    if (viewMode === 'month') {
      next.setMonth(next.getMonth() - 1);
    } else if (viewMode === 'week') {
      next.setDate(next.getDate() - 7);
    } else {
      next.setDate(next.getDate() - 1);
    }
    setCurrentDate(next);
  };

  const handleNext = () => {
    const next = new Date(currentDate);
    if (viewMode === 'month') {
      next.setMonth(next.getMonth() + 1);
    } else if (viewMode === 'week') {
      next.setDate(next.getDate() + 7);
    } else {
      next.setDate(next.getDate() + 1);
    }
    setCurrentDate(next);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleSelectDate = (date: Date) => {
    setCurrentDate(date);
    setViewMode('day');
  };

  // Slot and Item Click Handlers
  const handleSlotClick = (date: Date) => {
    setEditingEvent(null);
    setPrefillDate(date);
    setIsEventModalOpen(true);
  };

  const handleItemClick = (item: CalendarFeedItem) => {
    if (item.type === 'event') {
      setEditingEvent(item as CalendarEventItem);
      setPrefillDate(null);
      setIsEventModalOpen(true);
    } else {
      // Navigate to task details
      navigate(`/tasks/${item.id}`);
    }
  };

  // Event Modal Save/Delete callbacks
  const handleSaveEvent = async (
    payload: CalendarEventCreatePayload | CalendarEventUpdatePayload,
    eventId?: string
  ) => {
    if (eventId) {
      await calendarApi.updateEvent(eventId, payload as CalendarEventUpdatePayload);
    } else {
      await calendarApi.createEvent(payload as CalendarEventCreatePayload);
    }
    fetchFeed();
  };

  const handleDeleteEvent = async (eventId: string) => {
    await calendarApi.deleteEvent(eventId);
    fetchFeed();
  };

  // Task Scheduling callback
  const handleScheduleTask = async (payload: ScheduleTaskPayload) => {
    await calendarApi.scheduleTask(payload);
    fetchFeed();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Application Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link to="/dashboard" className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-500/20">
                DF
              </div>
              <span className="font-semibold text-lg tracking-tight text-white">
                DayFlow
              </span>
            </Link>

            <nav className="hidden sm:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/calendar"
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1.5"
              >
                <CalendarIcon className="w-3.5 h-3.5" />
                <span>Calendar</span>
              </Link>
              <Link
                to="/tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                <span>Tasks</span>
              </Link>
              <Link
                to="/projects"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Projects</span>
              </Link>
              <Link
                to="/recurring-tasks"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Recurring</span>
              </Link>
              <Link
                to="/activity"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Activity</span>
              </Link>
              <Link
                to="/analytics"
                className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 text-xs font-medium transition flex items-center gap-1.5"
              >
                <span>Analytics</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => logout()}
              disabled={authLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from this device"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>

            <button
              onClick={() => logoutAll()}
              disabled={authLoading}
              className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition flex items-center gap-1.5 text-xs font-medium disabled:opacity-50"
              title="Logout from all devices"
            >
              <span className="hidden sm:inline">Sign Out All</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 space-y-6">
        {/* Calendar Toolbar */}
        <CalendarToolbar
          currentDate={currentDate}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onPrev={handlePrev}
          onNext={handleNext}
          onToday={handleToday}
          onNewEvent={() => {
            setEditingEvent(null);
            setPrefillDate(new Date());
            setIsEventModalOpen(true);
          }}
          onScheduleTask={() => {
            setPrefillDate(new Date());
            setIsSchedulingModalOpen(true);
          }}
          onOpenFilters={() => setIsFilterDrawerOpen(true)}
          activeFilterCount={activeFilterCount}
        />

        {/* Error state banner with retry */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchFeed}
              className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-semibold transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading ? (
          <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
            <p className="text-sm text-slate-400">Loading your schedule...</p>
          </div>
        ) : (
          <div>
            {viewMode === 'month' && (
              <MonthView
                currentDate={currentDate}
                items={items}
                onSelectDate={handleSelectDate}
                onSlotClick={handleSlotClick}
                onItemClick={handleItemClick}
              />
            )}
            {viewMode === 'week' && (
              <WeekView
                currentDate={currentDate}
                items={items}
                onSelectDate={handleSelectDate}
                onSlotClick={handleSlotClick}
                onItemClick={handleItemClick}
              />
            )}
            {viewMode === 'day' && (
              <DayView
                currentDate={currentDate}
                items={items}
                onSlotClick={handleSlotClick}
                onItemClick={handleItemClick}
              />
            )}
          </div>
        )}
      </main>

      {/* Event Create / Edit Modal */}
      <CalendarEventModal
        isOpen={isEventModalOpen}
        event={editingEvent}
        prefillDate={prefillDate}
        onClose={() => setIsEventModalOpen(false)}
        onSave={handleSaveEvent}
        onDelete={handleDeleteEvent}
      />

      {/* Task Scheduling Modal */}
      <TaskSchedulingModal
        isOpen={isSchedulingModalOpen}
        prefillDate={prefillDate}
        onClose={() => setIsSchedulingModalOpen(false)}
        onSchedule={handleScheduleTask}
      />

      {/* Filter Drawer */}
      <CalendarFilterDrawer
        isOpen={isFilterDrawerOpen}
        filters={filters}
        onClose={() => setIsFilterDrawerOpen(false)}
        onApplyFilters={(newFilters) => setFilters(newFilters)}
        onResetFilters={() =>
          setFilters({
            includeTasks: true,
            includeEvents: true,
            projectId: null,
            categoryId: null,
            status: null,
            priority: null,
            recurringOnly: false,
          })
        }
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 text-center text-xs text-slate-500">
        DayFlow &bull; Stage 3B Internal Calendar &bull; Personal Workspace
      </footer>
    </div>
  );
};
