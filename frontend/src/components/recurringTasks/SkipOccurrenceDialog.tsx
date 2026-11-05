import React, { useState } from 'react';
import { AlertCircle, CalendarX, Loader2, X } from 'lucide-react';

interface SkipOccurrenceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (skipDate: string, reason?: string) => Promise<void>;
  defaultDate?: string | null;
}

export const SkipOccurrenceDialog: React.FC<SkipOccurrenceDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  defaultDate,
}) => {
  const [skipDate, setSkipDate] = useState(
    defaultDate || new Date().toISOString().split('T')[0]
  );
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (defaultDate) {
      setSkipDate(defaultDate);
    }
    setReason('');
    setError(null);
  }, [defaultDate, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skipDate) {
      setError('Date is required to skip.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onConfirm(skipDate, reason.trim() ? reason.trim() : undefined);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to skip occurrence.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 text-amber-400 mb-2">
          <CalendarX className="w-5 h-5" />
          <h3 className="text-base font-bold text-white">Skip Next Occurrence</h3>
        </div>

        <p className="text-xs text-slate-400 mb-4">
          Skipping this date will prevent a task occurrence from being generated and advance the schedule to the next period.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Date to Skip <span className="text-emerald-400">*</span>
            </label>
            <input
              type="date"
              required
              value={skipDate}
              onChange={(e) => setSkipDate(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Reason (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Vacation, Holiday, etc."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl border border-slate-800 hover:bg-slate-800/60 text-slate-400 hover:text-white text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs shadow-lg shadow-amber-500/20 transition flex items-center gap-1.5 disabled:opacity-50"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Confirm Skip</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

