import { apiClient } from './client';
import {
  FinancialAccount,
  FinancialAccountCreate,
  FinancialAccountUpdate,
  BalanceAdjustmentCreate,
  FinancialCategory,
  FinancialCategoryCreate,
  FinancialCategoryUpdate,
  FinancialTag,
  FinancialTagCreate,
  FinancialTransaction,
  FinancialTransactionCreate,
  FinancialTransactionUpdate,
  TransactionListResponse,
  FinancialTransfer,
  FinancialTransferCreate,
  Budget,
  BudgetCreate,
  BudgetUpdate,
  RecurringTransaction,
  RecurringTransactionCreate,
  RecurringTransactionUpdate,
  FinancialSavingsGoal,
  FinancialSavingsGoalCreate,
  FinancialSavingsGoalUpdate,
  SavingsGoalEntry,
  SavingsGoalEntryCreate,
  FinanceDashboardOverview,
  FinancialAnalyticsResponse,
} from '../types/finance';

export const financeApi = {
  // Accounts
  getAccounts: async (includeArchived: boolean = false): Promise<FinancialAccount[]> => {
    const res = await apiClient.get<FinancialAccount[]>('/api/v1/finance/accounts', {
      params: { include_archived: includeArchived },
    });
    return res.data;
  },

  createAccount: async (data: FinancialAccountCreate): Promise<FinancialAccount> => {
    const res = await apiClient.post<FinancialAccount>('/api/v1/finance/accounts', data);
    return res.data;
  },

  getAccount: async (accountId: string): Promise<FinancialAccount> => {
    const res = await apiClient.get<FinancialAccount>(`/api/v1/finance/accounts/${accountId}`);
    return res.data;
  },

  updateAccount: async (accountId: string, data: FinancialAccountUpdate): Promise<FinancialAccount> => {
    const res = await apiClient.put<FinancialAccount>(`/api/v1/finance/accounts/${accountId}`, data);
    return res.data;
  },

  archiveAccount: async (accountId: string, archive: boolean = true): Promise<FinancialAccount> => {
    const res = await apiClient.patch<FinancialAccount>(`/api/v1/finance/accounts/${accountId}/archive`, null, {
      params: { archive },
    });
    return res.data;
  },

  adjustBalance: async (accountId: string, data: BalanceAdjustmentCreate): Promise<FinancialAccount> => {
    const res = await apiClient.post<FinancialAccount>(`/api/v1/finance/accounts/${accountId}/adjust-balance`, data);
    return res.data;
  },

  // Categories & Tags
  getCategories: async (): Promise<FinancialCategory[]> => {
    const res = await apiClient.get<FinancialCategory[]>('/api/v1/finance/categories');
    return res.data;
  },

  createCategory: async (data: FinancialCategoryCreate): Promise<FinancialCategory> => {
    const res = await apiClient.post<FinancialCategory>('/api/v1/finance/categories', data);
    return res.data;
  },

  updateCategory: async (categoryId: string, data: FinancialCategoryUpdate): Promise<FinancialCategory> => {
    const res = await apiClient.put<FinancialCategory>(`/api/v1/finance/categories/${categoryId}`, data);
    return res.data;
  },

  deleteCategory: async (categoryId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/finance/categories/${categoryId}`);
  },

  getTags: async (): Promise<FinancialTag[]> => {
    const res = await apiClient.get<FinancialTag[]>('/api/v1/finance/tags');
    return res.data;
  },

  createTag: async (data: FinancialTagCreate): Promise<FinancialTag> => {
    const res = await apiClient.post<FinancialTag>('/api/v1/finance/tags', data);
    return res.data;
  },

  deleteTag: async (tagId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/finance/tags/${tagId}`);
  },

  // Transactions
  getTransactions: async (params?: {
    account_id?: string;
    category_id?: string;
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    include_voided?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<TransactionListResponse> => {
    const res = await apiClient.get<TransactionListResponse>('/api/v1/finance/transactions', { params });
    return res.data;
  },

  createTransaction: async (data: FinancialTransactionCreate): Promise<FinancialTransaction> => {
    const res = await apiClient.post<FinancialTransaction>('/api/v1/finance/transactions', data);
    return res.data;
  },

  getTransaction: async (txId: string): Promise<FinancialTransaction> => {
    const res = await apiClient.get<FinancialTransaction>(`/api/v1/finance/transactions/${txId}`);
    return res.data;
  },

  updateTransaction: async (txId: string, data: FinancialTransactionUpdate): Promise<FinancialTransaction> => {
    const res = await apiClient.put<FinancialTransaction>(`/api/v1/finance/transactions/${txId}`, data);
    return res.data;
  },

  voidTransaction: async (txId: string): Promise<FinancialTransaction> => {
    const res = await apiClient.post<FinancialTransaction>(`/api/v1/finance/transactions/${txId}/void`);
    return res.data;
  },

  // Transfers
  createTransfer: async (data: FinancialTransferCreate): Promise<FinancialTransfer> => {
    const res = await apiClient.post<FinancialTransfer>('/api/v1/finance/transfers', data);
    return res.data;
  },

  voidTransfer: async (transferId: string): Promise<FinancialTransfer> => {
    const res = await apiClient.post<FinancialTransfer>(`/api/v1/finance/transfers/${transferId}/void`);
    return res.data;
  },

  // Budgets
  getBudgets: async (year?: number, month?: number): Promise<Budget[]> => {
    const res = await apiClient.get<Budget[]>('/api/v1/finance/budgets', {
      params: { year, month },
    });
    return res.data;
  },

  createBudget: async (data: BudgetCreate): Promise<Budget> => {
    const res = await apiClient.post<Budget>('/api/v1/finance/budgets', data);
    return res.data;
  },

  updateBudget: async (budgetId: string, data: BudgetUpdate): Promise<Budget> => {
    const res = await apiClient.put<Budget>(`/api/v1/finance/budgets/${budgetId}`, data);
    return res.data;
  },

  deleteBudget: async (budgetId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/finance/budgets/${budgetId}`);
  },

  // Recurring Transactions
  getRecurringRules: async (): Promise<RecurringTransaction[]> => {
    const res = await apiClient.get<RecurringTransaction[]>('/api/v1/finance/recurring');
    return res.data;
  },

  createRecurringRule: async (data: RecurringTransactionCreate): Promise<RecurringTransaction> => {
    const res = await apiClient.post<RecurringTransaction>('/api/v1/finance/recurring', data);
    return res.data;
  },

  updateRecurringRule: async (ruleId: string, data: RecurringTransactionUpdate): Promise<RecurringTransaction> => {
    const res = await apiClient.put<RecurringTransaction>(`/api/v1/finance/recurring/${ruleId}`, data);
    return res.data;
  },

  deleteRecurringRule: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/finance/recurring/${ruleId}`);
  },

  // Savings Goals
  getSavingsGoals: async (): Promise<FinancialSavingsGoal[]> => {
    const res = await apiClient.get<FinancialSavingsGoal[]>('/api/v1/finance/savings-goals');
    return res.data;
  },

  createSavingsGoal: async (data: FinancialSavingsGoalCreate): Promise<FinancialSavingsGoal> => {
    const res = await apiClient.post<FinancialSavingsGoal>('/api/v1/finance/savings-goals', data);
    return res.data;
  },

  getSavingsGoal: async (goalId: string): Promise<FinancialSavingsGoal> => {
    const res = await apiClient.get<FinancialSavingsGoal>(`/api/v1/finance/savings-goals/${goalId}`);
    return res.data;
  },

  updateSavingsGoal: async (goalId: string, data: FinancialSavingsGoalUpdate): Promise<FinancialSavingsGoal> => {
    const res = await apiClient.put<FinancialSavingsGoal>(`/api/v1/finance/savings-goals/${goalId}`, data);
    return res.data;
  },

  deleteSavingsGoal: async (goalId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/finance/savings-goals/${goalId}`);
  },

  addSavingsEntry: async (goalId: string, data: SavingsGoalEntryCreate): Promise<SavingsGoalEntry> => {
    const res = await apiClient.post<SavingsGoalEntry>(`/api/v1/finance/savings-goals/${goalId}/entries`, data);
    return res.data;
  },

  // Overview & Analytics
  getOverview: async (): Promise<FinanceDashboardOverview> => {
    const res = await apiClient.get<FinanceDashboardOverview>('/api/v1/finance/overview');
    return res.data;
  },

  getAnalytics: async (currency: string = 'USD', startDate?: string, endDate?: string): Promise<FinancialAnalyticsResponse> => {
    const res = await apiClient.get<FinancialAnalyticsResponse>('/api/v1/finance/analytics', {
      params: { currency, start_date: startDate, end_date: endDate },
    });
    return res.data;
  },

  // CSV Export
  getExportCsvUrl: (params?: {
    account_id?: string;
    category_id?: string;
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
    include_voided?: boolean;
  }): string => {
    const query = new URLSearchParams();
    if (params?.account_id) query.append('account_id', params.account_id);
    if (params?.category_id) query.append('category_id', params.category_id);
    if (params?.transaction_type) query.append('transaction_type', params.transaction_type);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.include_voided !== undefined) query.append('include_voided', String(params.include_voided));
    return `/api/v1/finance/export/csv?${query.toString()}`;
  },
};
