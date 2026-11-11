import React from 'react';
import { Budget } from '../../types/finance';
import { AlertCircle, Trash2, Edit2 } from 'lucide-react';

interface BudgetCardProps {
  budget: Budget;
  onEdit: (budget: Budget) => void;
  onDelete: (budgetId: string) => void;
}

export const BudgetCard: React.FC<BudgetCardProps> = ({
  budget,
  onEdit,
  onDelete,
}) => {
  const percent = Math.min(budget.utilization_percentage, 100);
  const isOver = budget.is_overspent;
  const isWarning = !isOver && budget.utilization_percentage >= 80;

  const getProgressColor = () => {
    if (isOver) return 'bg-rose-500';
    if (isWarning) return 'bg-amber-500';
    return 'bg-indigo-600';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-gray-900 dark:text-white text-base">
            {budget.name}
          </h4>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {budget.category_name || 'Overall Spending'}
          </span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => onEdit(budget)}
            title="Edit Budget"
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(budget.id)}
            title="Delete Budget"
            className="p-1.5 text-gray-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-baseline mb-1.5">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Spent: <span className="text-gray-900 dark:text-white font-semibold">{budget.currency} {parseFloat(budget.actual_spending).toFixed(2)}</span>
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Budget: <span className="font-semibold">{budget.currency} {parseFloat(budget.amount).toFixed(2)}</span>
          </span>
        </div>

        <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${percent}%` }}
          />
        </div>

        <div className="mt-3 flex items-center justify-between text-xs">
          <span
            className={`font-medium ${
              isOver
                ? 'text-rose-600 dark:text-rose-400'
                : isWarning
                ? 'text-amber-600 dark:text-amber-400'
                : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {budget.utilization_percentage.toFixed(1)}% used
          </span>

          {isOver ? (
            <span className="flex items-center text-rose-600 dark:text-rose-400 font-medium space-x-1">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Over by {budget.currency} {parseFloat(budget.overspent_amount).toFixed(2)}</span>
            </span>
          ) : (
            <span className="text-gray-500 dark:text-gray-400">
              {budget.currency} {parseFloat(budget.remaining_amount).toFixed(2)} left
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
