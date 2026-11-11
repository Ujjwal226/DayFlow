import React from 'react';
import { FinancialAccount } from '../../types/finance';
import {
  Wallet,
  Landmark,
  PiggyBank,
  CreditCard,
  CircleDollarSign,
  Briefcase,
  Archive,
  ArrowUpDown,
  MoreVertical,
} from 'lucide-react';

interface AccountCardProps {
  account: FinancialAccount;
  onEdit: (account: FinancialAccount) => void;
  onArchive: (account: FinancialAccount) => void;
  onAdjustBalance: (account: FinancialAccount) => void;
}

export const AccountCard: React.FC<AccountCardProps> = ({
  account,
  onEdit,
  onArchive,
  onAdjustBalance,
}) => {
  const getIcon = () => {
    switch (account.account_type) {
      case 'CASH':
        return <Wallet className="w-5 h-5 text-emerald-500" />;
      case 'BANK_ACCOUNT':
        return <Landmark className="w-5 h-5 text-blue-500" />;
      case 'SAVINGS_ACCOUNT':
        return <PiggyBank className="w-5 h-5 text-purple-500" />;
      case 'CREDIT_CARD':
        return <CreditCard className="w-5 h-5 text-rose-500" />;
      case 'DIGITAL_WALLET':
        return <CircleDollarSign className="w-5 h-5 text-amber-500" />;
      default:
        return <Briefcase className="w-5 h-5 text-gray-500" />;
    }
  };

  const balanceNum = parseFloat(account.calculated_balance);
  const isCredit = account.account_type === 'CREDIT_CARD';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-gray-100 dark:bg-gray-700">
            {getIcon()}
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white text-base">
              {account.name}
            </h4>
            <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {account.account_type.replace('_', ' ').toLowerCase()}
              {account.institution_name ? ` • ${account.institution_name}` : ''}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => onAdjustBalance(account)}
            title="Adjust Balance"
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ArrowUpDown className="w-4 h-4" />
          </button>
          <button
            onClick={() => onArchive(account)}
            title={account.is_archived ? 'Unarchive' : 'Archive'}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Archive className="w-4 h-4" />
          </button>
          <button
            onClick={() => onEdit(account)}
            title="Edit"
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="mt-5">
        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
          {isCredit ? 'Balance Owed' : 'Current Balance'}
        </div>
        <div
          className={`text-2xl font-bold mt-1 ${
            isCredit
              ? balanceNum > 0
                ? 'text-rose-600 dark:text-rose-400'
                : 'text-gray-900 dark:text-white'
              : balanceNum < 0
              ? 'text-rose-600 dark:text-rose-400'
              : 'text-gray-900 dark:text-white'
          }`}
        >
          {account.currency} {parseFloat(account.calculated_balance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      {account.description && (
        <p className="mt-3 text-xs text-gray-500 dark:text-gray-400 truncate">
          {account.description}
        </p>
      )}
    </div>
  );
};
