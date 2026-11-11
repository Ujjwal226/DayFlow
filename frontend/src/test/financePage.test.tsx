import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { FinancePage } from '../pages/finance/FinancePage';
import { financeApi } from '../api/finance';

vi.mock('../api/finance', () => ({
  financeApi: {
    getOverview: vi.fn(),
    getAccounts: vi.fn(),
    getTransactions: vi.fn(),
    getBudgets: vi.fn(),
    getSavingsGoals: vi.fn(),
    getCategories: vi.fn(),
    getTags: vi.fn(),
    createAccount: vi.fn(),
    updateAccount: vi.fn(),
    archiveAccount: vi.fn(),
    adjustBalance: vi.fn(),
    createTransaction: vi.fn(),
    voidTransaction: vi.fn(),
    createTransfer: vi.fn(),
    createBudget: vi.fn(),
    deleteBudget: vi.fn(),
    addSavingsEntry: vi.fn(),
    getExportCsvUrl: vi.fn(() => '/api/v1/finance/export/csv'),
  },
}));

describe('FinancePage Component', () => {
  const mockOverview = {
    currencies: [
      {
        currency: 'USD',
        total_assets: '5000.00',
        total_liabilities: '1200.00',
        net_worth: '3800.00',
        income_this_month: '4000.00',
        expense_this_month: '1800.00',
        net_cash_flow_this_month: '2200.00',
      },
    ],
    accounts: [],
    recent_transactions: [],
    active_budgets: [],
    active_savings_goals: [],
  };

  const mockAccounts = [
    {
      id: 'acc-1',
      user_id: 'user-1',
      name: 'Primary Checking',
      account_type: 'BANK_ACCOUNT' as const,
      currency: 'USD',
      opening_balance: '1000.00',
      calculated_balance: '3500.00',
      description: 'Main checking',
      institution_name: 'Chase',
      color: null,
      icon: null,
      is_archived: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const mockTransactions = [
    {
      id: 'tx-1',
      user_id: 'user-1',
      account_id: 'acc-1',
      account_name: 'Primary Checking',
      category_id: 'cat-1',
      category_name: 'Groceries',
      transaction_type: 'EXPENSE' as const,
      amount: '85.50',
      currency: 'USD',
      description: 'Supermarket shopping',
      transaction_date: '2026-11-12',
      is_voided: false,
      tags: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const mockBudgets = [
    {
      id: 'b-1',
      user_id: 'user-1',
      name: 'Monthly Food Budget',
      category_name: 'Food & Dining',
      amount: '500.00',
      currency: 'USD',
      year: 2026,
      month: 11,
      actual_spending: '150.00',
      remaining_amount: '350.00',
      utilization_percentage: 30.0,
      is_overspent: false,
      overspent_amount: '0.00',
      is_archived: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const mockGoals = [
    {
      id: 'g-1',
      user_id: 'user-1',
      title: 'Emergency Fund',
      target_amount: '10000.00',
      currency: 'USD',
      current_amount: '4000.00',
      remaining_amount: '6000.00',
      progress_percentage: 40.0,
      status: 'ACTIVE' as const,
      entries: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(financeApi.getOverview).mockResolvedValue(mockOverview);
    vi.mocked(financeApi.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(financeApi.getTransactions).mockResolvedValue({
      items: mockTransactions,
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });
    vi.mocked(financeApi.getBudgets).mockResolvedValue(mockBudgets);
    vi.mocked(financeApi.getSavingsGoals).mockResolvedValue(mockGoals);
    vi.mocked(financeApi.getCategories).mockResolvedValue([]);
    vi.mocked(financeApi.getTags).mockResolvedValue([]);
  });

  it('renders finance page header and overview KPIs accurately', async () => {
    render(<FinancePage />);

    expect(screen.getByText('Personal Finance')).toBeInTheDocument();
    expect(screen.getByText('Multi-currency ledger, accounts, budgets, and savings goals')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Total Net Worth')).toBeInTheDocument();
      expect(screen.getByText('USD 3,800.00')).toBeInTheDocument();
      expect(screen.getByText('Income This Month')).toBeInTheDocument();
      expect(screen.getByText('Spending This Month')).toBeInTheDocument();
    });
  });

  it('displays active accounts and recent transactions table', async () => {
    render(<FinancePage />);

    await waitFor(() => {
      expect(screen.getAllByText('Primary Checking').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Supermarket shopping')).toBeInTheDocument();
      expect(screen.getByText('Groceries')).toBeInTheDocument();
      expect(screen.getByText('USD 3,500.00')).toBeInTheDocument();
    });
  });
});
