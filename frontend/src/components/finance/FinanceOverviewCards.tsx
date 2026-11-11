import React from 'react';
import { CurrencySummary } from '../../types/finance';
import { TrendingUp, TrendingDown, DollarSign, Wallet } from 'lucide-react';

interface FinanceOverviewCardsProps {
  currencies: CurrencySummary[];
  selectedCurrency: string;
  onSelectCurrency: (currency: string) => void;
}

export const FinanceOverviewCards: React.FC<FinanceOverviewCardsProps> = ({
  currencies,
  selectedCurrency,
  onSelectCurrency,
}) => {
  const currentSummary = currencies.find((c) => c.currency === selectedCurrency) || currencies[0];

  if (!currentSummary) {
    return null;
  }

  const netWorthNum = parseFloat(currentSummary.net_worth);
  const netCashFlowNum = parseFloat(currentSummary.net_cash_flow_this_month);

  return (
    <div className="space-y-4">
      {currencies.length > 1 && (
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Currency:</span>
          <div className="flex space-x-1">
            {currencies.map((c) => (
              <button
                key={c.currency}
                onClick={() => onSelectCurrency(c.currency)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  selectedCurrency === c.currency
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                }`}
              >
                {c.currency}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Worth */}
        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Net Worth</span>
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-2xl font-bold mt-2 ${netWorthNum < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-gray-900 dark:text-white'}`}>
            {currentSummary.currency} {parseFloat(currentSummary.net_worth).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Assets: {currentSummary.currency} {parseFloat(currentSummary.total_assets).toFixed(2)} • Liab: {currentSummary.currency} {parseFloat(currentSummary.total_liabilities).toFixed(2)}
          </div>
        </div>

        {/* Monthly Income */}
        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Income This Month</span>
            <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold mt-2 text-emerald-600 dark:text-emerald-400">
            +{currentSummary.currency} {parseFloat(currentSummary.income_this_month).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Authoritative cash inflows
          </div>
        </div>

        {/* Monthly Expenses */}
        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Spending This Month</span>
            <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold mt-2 text-rose-600 dark:text-rose-400">
            -{currentSummary.currency} {parseFloat(currentSummary.expense_this_month).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Non-transfer expenses
          </div>
        </div>

        {/* Net Cash Flow */}
        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Monthly Net Savings</span>
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-2xl font-bold mt-2 ${netCashFlowNum >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-rose-600 dark:text-rose-400'}`}>
            {netCashFlowNum >= 0 ? '+' : ''}{currentSummary.currency} {parseFloat(currentSummary.net_cash_flow_this_month).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {netCashFlowNum >= 0 ? 'Positive savings rate' : 'Deficit this month'}
          </div>
        </div>
      </div>
    </div>
  );
};
