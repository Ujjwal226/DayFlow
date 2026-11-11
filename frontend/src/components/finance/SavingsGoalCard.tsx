import React from 'react';
import { FinancialSavingsGoal } from '../../types/finance';
import { PlusCircle, Target, CheckCircle2, Calendar } from 'lucide-react';

interface SavingsGoalCardProps {
  goal: FinancialSavingsGoal;
  onAddEntry: (goal: FinancialSavingsGoal) => void;
  onEdit: (goal: FinancialSavingsGoal) => void;
  onDelete: (goalId: string) => void;
}

export const SavingsGoalCard: React.FC<SavingsGoalCardProps> = ({
  goal,
  onAddEntry,
}) => {
  const percent = Math.min(goal.progress_percentage, 100);
  const isCompleted = goal.status === 'COMPLETED' || percent >= 100;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-lg ${isCompleted ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400' : 'bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400'}`}>
            {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : <Target className="w-5 h-5" />}
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white text-base">
              {goal.title}
            </h4>
            {goal.target_date && (
              <span className="flex items-center text-xs text-gray-500 dark:text-gray-400 space-x-1 mt-0.5">
                <Calendar className="w-3.5 h-3.5" />
                <span>Target: {goal.target_date}</span>
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => onAddEntry(goal)}
          className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 rounded-lg transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Contribute</span>
        </button>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-baseline mb-1.5">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Saved: <span className="text-gray-900 dark:text-white font-semibold">{goal.currency} {parseFloat(goal.current_amount).toFixed(2)}</span>
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Goal: <span className="font-semibold">{goal.currency} {parseFloat(goal.target_amount).toFixed(2)}</span>
          </span>
        </div>

        <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${isCompleted ? 'bg-emerald-500' : 'bg-indigo-600'}`}
            style={{ width: `${percent}%` }}
          />
        </div>

        <div className="mt-3 flex items-center justify-between text-xs">
          <span className={`font-semibold ${isCompleted ? 'text-emerald-600 dark:text-emerald-400' : 'text-indigo-600 dark:text-indigo-400'}`}>
            {goal.progress_percentage.toFixed(1)}% achieved
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            {isCompleted ? 'Target achieved!' : `${goal.currency} ${parseFloat(goal.remaining_amount).toFixed(2)} remaining`}
          </span>
        </div>
      </div>
    </div>
  );
};
