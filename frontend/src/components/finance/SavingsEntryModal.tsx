import React, { useState } from 'react';
import { FinancialSavingsGoal, SavingsGoalEntryCreate } from '../../types/finance';
import { X } from 'lucide-react';

interface SavingsEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (goalId: string, data: SavingsGoalEntryCreate) => Promise<void>;
  goal: FinancialSavingsGoal | null;
}

export const SavingsEntryModal: React.FC<SavingsEntryModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  goal,
}) => {
  const [entryType, setEntryType] = useState<'DEPOSIT' | 'WITHDRAWAL'>('DEPOSIT');
  const [amount, setAmount] = useState('');
  const [entryDate, setEntryDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !goal) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit(goal.id, {
        entry_type: entryType,
        amount: amount,
        entry_date: entryDate,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Failed to record entry';
      setError(msg || 'Failed to record entry');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-sm w-full p-6 shadow-xl border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Savings Contribution
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/30 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
              Goal: <span className="font-semibold text-gray-800 dark:text-gray-200">{goal.title}</span>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Current Saved: <span className="font-semibold text-gray-800 dark:text-gray-200">{goal.currency} {parseFloat(goal.current_amount).toFixed(2)}</span>
            </div>
          </div>

          <div className="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1">
            <button
              type="button"
              onClick={() => setEntryType('DEPOSIT')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                entryType === 'DEPOSIT'
                  ? 'bg-emerald-500 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300'
              }`}
            >
              Deposit / Add
            </button>
            <button
              type="button"
              onClick={() => setEntryType('WITHDRAWAL')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                entryType === 'WITHDRAWAL'
                  ? 'bg-rose-500 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300'
              }`}
            >
              Withdrawal
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Amount ({goal.currency}) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none font-semibold"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date *
              </label>
              <input
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Note
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Birthday bonus allocation"
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg font-medium shadow-sm"
            >
              {loading ? 'Saving...' : 'Record Contribution'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
