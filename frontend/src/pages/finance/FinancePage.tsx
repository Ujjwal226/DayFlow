import React, { useState, useEffect, useCallback } from 'react';
import { financeApi } from '../../api/finance';
import {
  FinanceDashboardOverview,
  FinancialAccount,
  FinancialAccountCreate,
  FinancialTransaction,
  FinancialTransactionCreate,
  FinancialTransferCreate,
  Budget,
  BudgetCreate,
  FinancialSavingsGoal,
  FinancialCategory,
  FinancialTag,
  BalanceAdjustmentCreate,
  SavingsGoalEntryCreate,
} from '../../types/finance';
import { FinanceOverviewCards } from '../../components/finance/FinanceOverviewCards';
import { AccountCard } from '../../components/finance/AccountCard';
import { AccountModal } from '../../components/finance/AccountModal';
import { AdjustmentModal } from '../../components/finance/AdjustmentModal';
import { TransactionTable } from '../../components/finance/TransactionTable';
import { TransactionModal } from '../../components/finance/TransactionModal';
import { TransferModal } from '../../components/finance/TransferModal';
import { BudgetCard } from '../../components/finance/BudgetCard';
import { BudgetModal } from '../../components/finance/BudgetModal';
import { SavingsGoalCard } from '../../components/finance/SavingsGoalCard';
import { SavingsEntryModal } from '../../components/finance/SavingsEntryModal';
import {
  Plus,
  ArrowRightLeft,
  Download,
  Wallet,
  PieChart,
  Target,
} from 'lucide-react';

export const FinancePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'ACCOUNTS' | 'TRANSACTIONS' | 'BUDGETS' | 'SAVINGS'>('OVERVIEW');
  const [overview, setOverview] = useState<FinanceDashboardOverview | null>(null);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [savingsGoals, setSavingsGoals] = useState<FinancialSavingsGoal[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);
  const [tags, setTags] = useState<FinancialTag[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<FinancialAccount | null>(null);
  const [isAdjustmentModalOpen, setIsAdjustmentModalOpen] = useState(false);
  const [adjustingAccount, setAdjustingAccount] = useState<FinancialAccount | null>(null);
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isSavingsEntryModalOpen, setIsSavingsEntryModalOpen] = useState(false);
  const [selectedSavingsGoal, setSelectedSavingsGoal] = useState<FinancialSavingsGoal | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ovData, accData, txData, bData, sgData, catData, tagData] = await Promise.all([
        financeApi.getOverview(),
        financeApi.getAccounts(true),
        financeApi.getTransactions({ page_size: 50 }),
        financeApi.getBudgets(),
        financeApi.getSavingsGoals(),
        financeApi.getCategories(),
        financeApi.getTags(),
      ]);
      setOverview(ovData);
      setAccounts(accData);
      setTransactions(txData.items);
      setBudgets(bData);
      setSavingsGoals(sgData);
      setCategories(catData);
      setTags(tagData);

      if (ovData.currencies.length > 0 && !ovData.currencies.some((c) => c.currency === selectedCurrency)) {
        setSelectedCurrency(ovData.currencies[0].currency);
      }
    } catch (err) {
      console.error('Failed to load finance data', err);
    } finally {
      setLoading(false);
    }
  }, [selectedCurrency]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateAccount = async (data: FinancialAccountCreate) => {
    if (editingAccount) {
      await financeApi.updateAccount(editingAccount.id, data);
    } else {
      await financeApi.createAccount(data);
    }
    setEditingAccount(null);
    loadData();
  };

  const handleArchiveAccount = async (account: FinancialAccount) => {
    await financeApi.archiveAccount(account.id, !account.is_archived);
    loadData();
  };

  const handleAdjustBalance = async (accountId: string, data: BalanceAdjustmentCreate) => {
    await financeApi.adjustBalance(accountId, data);
    loadData();
  };

  const handleCreateTransaction = async (data: FinancialTransactionCreate) => {
    await financeApi.createTransaction(data);
    loadData();
  };

  const handleVoidTransaction = async (txId: string) => {
    if (window.confirm('Are you sure you want to void this transaction? This will reverse its effect on account balance.')) {
      await financeApi.voidTransaction(txId);
      loadData();
    }
  };

  const handleCreateTransfer = async (data: FinancialTransferCreate) => {
    await financeApi.createTransfer(data);
    loadData();
  };

  const handleCreateBudget = async (data: BudgetCreate) => {
    await financeApi.createBudget(data);
    loadData();
  };

  const handleDeleteBudget = async (budgetId: string) => {
    if (window.confirm('Delete this budget?')) {
      await financeApi.deleteBudget(budgetId);
      loadData();
    }
  };

  const handleAddSavingsEntry = async (goalId: string, data: SavingsGoalEntryCreate) => {
    await financeApi.addSavingsEntry(goalId, data);
    loadData();
  };

  const handleExportCsv = () => {
    window.open(financeApi.getExportCsvUrl(), '_blank');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Personal Finance
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Multi-currency ledger, accounts, budgets, and savings goals
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportCsv}
            className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 shadow-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setIsTransferModalOpen(true)}
            disabled={accounts.length < 2}
            className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 shadow-sm transition-colors"
          >
            <ArrowRightLeft className="w-4 h-4" />
            <span>Transfer</span>
          </button>
          <button
            onClick={() => setIsTransactionModalOpen(true)}
            disabled={accounts.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Transaction</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      {overview && (
        <FinanceOverviewCards
          currencies={overview.currencies}
          selectedCurrency={selectedCurrency}
          onSelectCurrency={setSelectedCurrency}
        />
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-4">
          <button
            onClick={() => setActiveTab('OVERVIEW')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'OVERVIEW'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('ACCOUNTS')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'ACCOUNTS'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Accounts ({accounts.filter((a) => !a.is_archived).length})
          </button>
          <button
            onClick={() => setActiveTab('TRANSACTIONS')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'TRANSACTIONS'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Transactions
          </button>
          <button
            onClick={() => setActiveTab('BUDGETS')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'BUDGETS'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Budgets ({budgets.length})
          </button>
          <button
            onClick={() => setActiveTab('SAVINGS')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'SAVINGS'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            Savings Goals ({savingsGoals.length})
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Active Accounts preview */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                Accounts
              </h3>
              <button
                onClick={() => {
                  setEditingAccount(null);
                  setIsAccountModalOpen(true);
                }}
                className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                + Add Account
              </button>
            </div>
            {accounts.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 p-8 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
                <Wallet className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No financial accounts yet</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Add your checking, savings, or cash accounts to track net worth</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {accounts.filter((a) => !a.is_archived).slice(0, 3).map((account) => (
                  <AccountCard
                    key={account.id}
                    account={account}
                    onEdit={(acc) => {
                      setEditingAccount(acc);
                      setIsAccountModalOpen(true);
                    }}
                    onArchive={handleArchiveAccount}
                    onAdjustBalance={(acc) => {
                      setAdjustingAccount(acc);
                      setIsAdjustmentModalOpen(true);
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Recent transactions preview */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                Recent Transactions
              </h3>
              <button
                onClick={() => setActiveTab('TRANSACTIONS')}
                className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                View All
              </button>
            </div>
            <TransactionTable
              transactions={transactions.slice(0, 8)}
              onVoid={handleVoidTransaction}
              loading={loading}
            />
          </div>
        </div>
      )}

      {activeTab === 'ACCOUNTS' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => {
                setEditingAccount(null);
                setIsAccountModalOpen(true);
              }}
              className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Account</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                onEdit={(acc) => {
                  setEditingAccount(acc);
                  setIsAccountModalOpen(true);
                }}
                onArchive={handleArchiveAccount}
                onAdjustBalance={(acc) => {
                  setAdjustingAccount(acc);
                  setIsAdjustmentModalOpen(true);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'TRANSACTIONS' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
          <TransactionTable
            transactions={transactions}
            onVoid={handleVoidTransaction}
            loading={loading}
          />
        </div>
      )}

      {activeTab === 'BUDGETS' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setIsBudgetModalOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create Budget</span>
            </button>
          </div>
          {budgets.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 p-8 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
              <PieChart className="w-10 h-10 text-gray-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No monthly budgets configured</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Set spending targets and receive alerts before exceeding them</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {budgets.map((b) => (
                <BudgetCard
                  key={b.id}
                  budget={b}
                  onEdit={() => {}}
                  onDelete={handleDeleteBudget}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'SAVINGS' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => {}}
              className="inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>New Savings Goal</span>
            </button>
          </div>
          {savingsGoals.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 p-8 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
              <Target className="w-10 h-10 text-gray-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No active savings targets</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Track funds allocated for an emergency fund, travel, or milestone goals</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savingsGoals.map((g) => (
                <SavingsGoalCard
                  key={g.id}
                  goal={g}
                  onAddEntry={(goal) => {
                    setSelectedSavingsGoal(goal);
                    setIsSavingsEntryModalOpen(true);
                  }}
                  onEdit={() => {}}
                  onDelete={() => {}}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <AccountModal
        isOpen={isAccountModalOpen}
        onClose={() => {
          setIsAccountModalOpen(false);
          setEditingAccount(null);
        }}
        onSubmit={handleCreateAccount}
        initialData={editingAccount}
      />

      <AdjustmentModal
        isOpen={isAdjustmentModalOpen}
        onClose={() => {
          setIsAdjustmentModalOpen(false);
          setAdjustingAccount(null);
        }}
        onSubmit={handleAdjustBalance}
        account={adjustingAccount}
      />

      <TransactionModal
        isOpen={isTransactionModalOpen}
        onClose={() => setIsTransactionModalOpen(false)}
        onSubmit={handleCreateTransaction}
        accounts={accounts.filter((a) => !a.is_archived)}
        categories={categories}
        tags={tags}
      />

      <TransferModal
        isOpen={isTransferModalOpen}
        onClose={() => setIsTransferModalOpen(false)}
        onSubmit={handleCreateTransfer}
        accounts={accounts.filter((a) => !a.is_archived)}
      />

      <BudgetModal
        isOpen={isBudgetModalOpen}
        onClose={() => setIsBudgetModalOpen(false)}
        onSubmit={handleCreateBudget}
        categories={categories}
      />

      <SavingsEntryModal
        isOpen={isSavingsEntryModalOpen}
        onClose={() => {
          setIsSavingsEntryModalOpen(false);
          setSelectedSavingsGoal(null);
        }}
        onSubmit={handleAddSavingsEntry}
        goal={selectedSavingsGoal}
      />
    </div>
  );
};
