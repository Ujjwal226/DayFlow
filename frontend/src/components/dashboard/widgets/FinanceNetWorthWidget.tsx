import React, { useEffect, useState } from 'react';
import { WidgetProps } from '../../../types/dashboard';
import { financeApi } from '../../../api/finance';
import { FinanceDashboardOverview } from '../../../types/finance';
import { DollarSign } from 'lucide-react';
import { Link } from 'react-router-dom';

export const FinanceNetWorthWidget: React.FC<WidgetProps> = () => {
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
        Loading financial status...
      </div>
    );
  }

  const primarySummary = overview?.currencies[0];

  if (!primarySummary) {
    return (
      <div className="p-4 text-center">
        <p className="text-xs text-slate-400">No accounts configured yet.</p>
        <Link
          to="/finance"
          className="text-xs text-emerald-400 hover:underline mt-1 inline-block"
        >
          Set up finance accounts &rarr;
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 font-medium">Net Worth</span>
          <div className="text-xl font-bold text-white mt-0.5">
            {primarySummary.currency} {parseFloat(primarySummary.net_worth).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <DollarSign className="w-5 h-5" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
        <div>
          <span className="text-slate-500">Assets</span>
          <div className="font-semibold text-slate-300">
            {primarySummary.currency} {parseFloat(primarySummary.total_assets).toFixed(2)}
          </div>
        </div>
        <div>
          <span className="text-slate-500">Liabilities</span>
          <div className="font-semibold text-slate-300">
            {primarySummary.currency} {parseFloat(primarySummary.total_liabilities).toFixed(2)}
          </div>
        </div>
      </div>

      <div className="pt-1 flex justify-end">
        <Link
          to="/finance"
          className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          View Full Portfolio &rarr;
        </Link>
      </div>
    </div>
  );
};
