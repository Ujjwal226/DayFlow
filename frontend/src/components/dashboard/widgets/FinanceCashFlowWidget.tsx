import React, { useEffect, useState } from 'react';
import { WidgetProps } from '../../../types/dashboard';
import { financeApi } from '../../../api/finance';
import { FinanceDashboardOverview } from '../../../types/finance';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Link } from 'react-router-dom';

export const FinanceCashFlowWidget: React.FC<WidgetProps> = () => {
  const [overview, setOverview] = useState<FinanceDashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    financeApi
      .getOverview()
      .then((data) => {
        if (mounted) setOverview(data);
      })
      .catch(() => {})
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center text-xs text-slate-400">
        Loading cash flow...
      </div>
    );
  }

  const primarySummary = overview?.currencies[0];

  if (!primarySummary) {
    return (
      <div className="p-4 text-center">
        <p className="text-xs text-slate-400">No transactions recorded this month.</p>
        <Link
          to="/finance"
          className="text-xs text-emerald-400 hover:underline mt-1 inline-block"
        >
          Record income or expenses &rarr;
        </Link>
      </div>
    );
  }

  const netSavings = parseFloat(primarySummary.net_cash_flow_this_month);

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 font-medium">Monthly Cash Flow</span>
          <div
            className={`text-xl font-bold mt-0.5 ${
              netSavings >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {netSavings >= 0 ? '+' : ''}
            {primarySummary.currency} {netSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
        <div className="flex items-center space-x-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          <div>
            <span className="text-slate-500 block">Income</span>
            <span className="font-semibold text-emerald-400">
              +{primarySummary.currency} {parseFloat(primarySummary.income_this_month).toFixed(2)}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-1.5">
          <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
          <div>
            <span className="text-slate-500 block">Spending</span>
            <span className="font-semibold text-rose-400">
              -{primarySummary.currency} {parseFloat(primarySummary.expense_this_month).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="pt-1 flex justify-end">
        <Link
          to="/finance"
          className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          View Cash Flow Trends &rarr;
        </Link>
      </div>
    </div>
  );
};
