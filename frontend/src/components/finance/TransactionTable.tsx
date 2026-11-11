import React from 'react';
import { FinancialTransaction } from '../../types/finance';
import { ArrowDownLeft, ArrowUpRight, RefreshCw, SlidersHorizontal, Ban } from 'lucide-react';

interface TransactionTableProps {
  transactions: FinancialTransaction[];
  onVoid: (txId: string) => void;
  loading?: boolean;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  transactions,
  onVoid,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
        Loading transactions...
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
        No transactions found matching your criteria.
      </div>
    );
  }

  const getTypeIcon = (tx: FinancialTransaction) => {
    switch (tx.transaction_type) {
      case 'INCOME':
        return <ArrowDownLeft className="w-4 h-4 text-emerald-500" />;
      case 'EXPENSE':
        return <ArrowUpRight className="w-4 h-4 text-rose-500" />;
      case 'TRANSFER':
        return <RefreshCw className="w-4 h-4 text-blue-500" />;
      case 'ADJUSTMENT':
        return <SlidersHorizontal className="w-4 h-4 text-amber-500" />;
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 dark:bg-gray-700/50 text-xs font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
          <tr>
            <th className="py-3 px-4">Date</th>
            <th className="py-3 px-4">Description</th>
            <th className="py-3 px-4">Category</th>
            <th className="py-3 px-4">Account</th>
            <th className="py-3 px-4 text-right">Amount</th>
            <th className="py-3 px-4 text-center">Status</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {transactions.map((tx) => {
            const isIncome = tx.transaction_type === 'INCOME';
            const isExpense = tx.transaction_type === 'EXPENSE';
            const numAmount = parseFloat(tx.amount);

            return (
              <tr
                key={tx.id}
                className={`hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors ${
                  tx.is_voided ? 'opacity-50 line-through' : ''
                }`}
              >
                <td className="py-3 px-4 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                  {tx.transaction_date}
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center space-x-2">
                    <div className="p-1 rounded-md bg-gray-100 dark:bg-gray-800">
                      {getTypeIcon(tx)}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {tx.description}
                      </div>
                      {tx.merchant_or_source && (
                        <div className="text-xs text-gray-400 dark:text-gray-500">
                          {tx.merchant_or_source}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                    {tx.category_name || 'Uncategorized'}
                  </span>
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-xs text-gray-600 dark:text-gray-300">
                  {tx.account_name || 'Account'}
                </td>
                <td
                  className={`py-3 px-4 whitespace-nowrap text-right font-semibold ${
                    isIncome
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : isExpense
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-gray-900 dark:text-white'
                  }`}
                >
                  {isIncome ? '+' : isExpense ? '-' : ''}
                  {tx.currency} {numAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-center">
                  {tx.is_voided ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300">
                      Voided
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                      Completed
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 whitespace-nowrap text-right">
                  {!tx.is_voided && (
                    <button
                      onClick={() => onVoid(tx.id)}
                      title="Void transaction"
                      className="p-1 text-gray-400 hover:text-rose-600 dark:hover:text-rose-400 rounded transition-colors"
                    >
                      <Ban className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
