/** Shared utility helpers */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Date / time ─────────────────────────────────────────────────────────────

/** Format "YYYY-MM-DD" → "Mon, 15 Oct 2026" */
export function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/** Format ISO UTC timestamp to Asia/Kolkata date & time */
export function formatUTCDateTime(isoStr: string | null | undefined): string {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

/** Format "HH:MM:SS" → "09:00 AM" */
export function formatTime(timeStr: string | null): string {
  if (!timeStr) return '';
  const [h, m] = timeStr.split(':').map(Number);
  const d = new Date();
  d.setHours(h, m, 0, 0);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
}

/** Today's date in Asia/Kolkata as "YYYY-MM-DD" */
export function todayISO(): string {
  // Use en-CA locale for ISO standard YYYY-MM-DD with Asia/Kolkata timeZone
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}

/** Get next or previous date ISO string from given "YYYY-MM-DD" */
export function shiftDateISO(dateStr: string, days: number): string {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  dt.setDate(dt.getDate() + days);
  const year = dt.getFullYear();
  const month = String(dt.getMonth() + 1).padStart(2, '0');
  const day = String(dt.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Compare two "YYYY-MM-DD" strings */
export function isOverdue(scheduledDate: string, status: string): boolean {
  return status === 'pending' && scheduledDate < todayISO();
}

export function isToday(scheduledDate: string): boolean {
  return scheduledDate === todayISO();
}

/** "YYYY-MM-DD" → <input type="date"> value (already correct format) */
export function toInputDate(dateStr: string | null | undefined): string {
  return dateStr ?? '';
}

/** "HH:MM:SS" → "HH:MM" for <input type="time"> */
export function toInputTime(timeStr: string | null | undefined): string {
  if (!timeStr) return '';
  return timeStr.slice(0, 5);
}

/** "HH:MM" → "HH:MM:00" for API */
export function fromInputTime(val: string): string | null {
  return val ? `${val}:00` : null;
}

// ─── Label helpers ────────────────────────────────────────────────────────────

export const PRIORITY_LABELS: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
};

export const CATEGORY_LABELS: Record<string, string> = {
  work: 'Work',
  personal: 'Personal',
  learning: 'Learning',
  health: 'Health',
  other: 'Other',
};

export const PRIORITY_COLORS: Record<string, string> = {
  low:    'text-blue-400 bg-blue-400/10',
  medium: 'text-yellow-400 bg-yellow-400/10',
  high:   'text-red-400 bg-red-400/10',
};

export const CATEGORY_COLORS: Record<string, string> = {
  work:     'text-violet-400 bg-violet-400/10',
  personal: 'text-pink-400 bg-pink-400/10',
  learning: 'text-cyan-400 bg-cyan-400/10',
  health:   'text-green-400 bg-green-400/10',
  other:    'text-slate-400 bg-slate-400/10',
};

// Light-theme variants (used in light mode)
export const PRIORITY_COLORS_LIGHT: Record<string, string> = {
  low:    'text-blue-700 bg-blue-100',
  medium: 'text-yellow-700 bg-yellow-100',
  high:   'text-red-700 bg-red-100',
};

export const CATEGORY_COLORS_LIGHT: Record<string, string> = {
  work:     'text-violet-700 bg-violet-100',
  personal: 'text-pink-700 bg-pink-100',
  learning: 'text-cyan-700 bg-cyan-100',
  health:   'text-green-700 bg-green-100',
  other:    'text-slate-600 bg-slate-100',
};
