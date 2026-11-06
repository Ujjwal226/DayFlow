import React, { useState, useEffect } from 'react';
import { CalendarEventCreatePayload, CalendarEventItem, CalendarEventUpdatePayload } from '../../types/calendar';
import { X, Calendar as CalendarIcon, Clock, MapPin, Palette, Trash2, AlertCircle } from 'lucide-react';

interface CalendarEventModalProps {
  isOpen: boolean;
  event: CalendarEventItem | null; // null if creating
  prefillDate?: Date | null;
  onClose: () => void;
  onSave: (payload: CalendarEventCreatePayload | CalendarEventUpdatePayload, eventId?: string) => Promise<void>;
  onDelete?: (eventId: string) => Promise<void>;
}

export const CalendarEventModal: React.FC<CalendarEventModalProps> = ({
  isOpen,
  event,
  prefillDate,
  onClose,
  onSave,
  onDelete,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [isAllDay, setIsAllDay] = useState(false);
  const [startDateStr, setStartDateStr] = useState('');
  const [endDateStr, setEndDateStr] = useState('');
  const [startTimeStr, setStartTimeStr] = useState('');
  const [endTimeStr, setEndTimeStr] = useState('');
  const [timezoneStr, setTimezoneStr] = useState('UTC');

  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize or reset form state
  useEffect(() => {
    if (!isOpen) return;

    setError(null);
    setConfirmDelete(false);
    const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    setTimezoneStr(userTz);

    if (event) {
      setTitle(event.title);
      setDescription(event.description || '');
      setLocation(event.location || '');
      setColor(event.color || '#3B82F6');
      setIsAllDay(event.is_all_day);
      setTimezoneStr(event.timezone || userTz);

      if (event.is_all_day && event.start_date && event.end_date) {
        setStartDateStr(event.start_date);
        setEndDateStr(event.end_date);
      } else if (event.start_at && event.end_at) {
        const s = new Date(event.start_at);
        const e = new Date(event.end_at);
        setStartDateStr(s.toISOString().slice(0, 10));
        setStartTimeStr(s.toTimeString().slice(0, 5));
        setEndDateStr(e.toISOString().slice(0, 10));
        setEndTimeStr(e.toTimeString().slice(0, 5));
      }
    } else {
      // Creating new event
      setTitle('');
      setDescription('');
      setLocation('');
      setColor('#3B82F6');
      setIsAllDay(false);

      const base = prefillDate || new Date();
      const sDate = base.toISOString().slice(0, 10);
      setStartDateStr(sDate);
      setEndDateStr(sDate);

      // Default 1-hour slot
      const nowH = base.getHours();
      setStartTimeStr(`${String(nowH).padStart(2, '0')}:00`);
      setEndTimeStr(`${String(nowH + 1).padStart(2, '0')}:00`);
    }
  }, [isOpen, event, prefillDate]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError('Title cannot be empty.');
      return;
    }

    if (isAllDay) {
      if (!startDateStr || !endDateStr) {
        setError('Both start date and exclusive end date are required.');
        return;
      }
      if (endDateStr <= startDateStr) {
        setError('Exclusive end date must be strictly after start date.');
        return;
      }

      setIsSaving(true);
      try {
        await onSave(
          {
            title: trimmedTitle,
            description: description.trim() || null,
            location: location.trim() || null,
            color,
            is_all_day: true,
            timezone: timezoneStr,
            start_date: startDateStr,
            end_date: endDateStr,
            start_at: null,
            end_at: null,
          },
          event?.id
        );
        onClose();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to save event.';
        setError(msg);
      } finally {
        setIsSaving(false);
      }
    } else {
      // Timed event
      if (!startDateStr || !startTimeStr || !endDateStr || !endTimeStr) {
        setError('Please specify start and end dates and times.');
        return;
      }

      const startDt = new Date(`${startDateStr}T${startTimeStr}:00`);
      const endDt = new Date(`${endDateStr}T${endTimeStr}:00`);

      if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
        setError('Invalid date or time entered.');
        return;
      }

      if (endDt <= startDt) {
        setError('End time must be strictly after start time.');
        return;
      }

      setIsSaving(true);
      try {
        await onSave(
          {
            title: trimmedTitle,
            description: description.trim() || null,
            location: location.trim() || null,
            color,
            is_all_day: false,
            timezone: timezoneStr,
            start_at: startDt.toISOString(),
            end_at: endDt.toISOString(),
            start_date: null,
            end_date: null,
          },
          event?.id
        );
        onClose();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to save event.';
        setError(msg);
      } finally {
        setIsSaving(false);
      }
    }
  };

  const handleDelete = async () => {
    if (!event || !onDelete) return;
    setIsDeleting(true);
    try {
      await onDelete(event.id);
      onClose();
    } catch {
      setError('Failed to delete event.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="calendar-modal-title"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 id="calendar-modal-title" className="text-base font-bold text-white flex items-center gap-2">
            <CalendarIcon className="w-4 h-4 text-emerald-400" />
            <span>{event ? 'Edit Calendar Event' : 'Create Calendar Event'}</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Meeting with product team"
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            />
          </div>

          {/* All-Day Switch */}
          <div className="flex items-center justify-between pt-1 pb-1">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>All-Day Event</span>
            </span>
            <button
              type="button"
              onClick={() => setIsAllDay(!isAllDay)}
              className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                isAllDay ? 'bg-emerald-500' : 'bg-slate-700'
              }`}
              role="switch"
              aria-checked={isAllDay}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  isAllDay ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Date & Time fields */}
          {isAllDay ? (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDateStr}
                  onChange={(e) => setStartDateStr(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Exclusive End Date</label>
                <input
                  type="date"
                  value={endDateStr}
                  onChange={(e) => setEndDateStr(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={startDateStr}
                    onChange={(e) => setStartDateStr(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={startTimeStr}
                    onChange={(e) => setStartTimeStr(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDateStr}
                    onChange={(e) => setEndDateStr(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">End Time</label>
                  <input
                    type="time"
                    value={endTimeStr}
                    onChange={(e) => setEndTimeStr(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
              </div>
            </div>
          )}

          {/* Location & Color */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                <span>Location</span>
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Google Meet or Room 102"
                className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-xs placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1">
                <Palette className="w-3 h-3" />
                <span>Color</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="w-8 h-8 rounded-lg bg-transparent border border-slate-700 cursor-pointer p-0.5"
                />
                <span className="text-xs font-mono text-slate-300 uppercase">{color}</span>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Agenda or notes..."
              className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-xs focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Action buttons */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            {event && onDelete ? (
              confirmDelete ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-rose-400 font-semibold">Confirm delete?</span>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold"
                  >
                    {isDeleting ? 'Deleting...' : 'Yes, Delete'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    className="px-2 py-1 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmDelete(true)}
                  className="px-3 py-1.5 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Event</span>
                </button>
              )
            ) : (
              <div />
            )}

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : event ? 'Update Event' : 'Create Event'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

