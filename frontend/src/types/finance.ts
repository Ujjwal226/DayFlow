export type FinancialAccountType =
  | 'CASH'
  | 'BANK_ACCOUNT'
  | 'SAVINGS_ACCOUNT'
  | 'CREDIT_CARD'
  | 'DIGITAL_WALLET'
  | 'CUSTOM';

export type FinancialTransactionType = 'INCOME' | 'EXPENSE' | 'TRANSFER' | 'ADJUSTMENT';

export type FinancialCategoryType = 'INCOME' | 'EXPENSE';

export type RecurringFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY';

export type SavingsGoalStatus = 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';

export interface FinancialAccount {
  id: string;
  user_id: string;
  name: string;
  account_type: FinancialAccountType;
  currency: string;
  opening_balance: string;
  calculated_balance: string;
  description?: string | null;
  institution_name?: string | null;
  color?: string | null;
  icon?: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface FinancialAccountCreate {
  name: string;
  account_type: FinancialAccountType;
  currency: string;
  opening_balance: string;
  description?: string | null;
  institution_name?: string | null;
  color?: string | null;
  icon?: string | null;
}

export interface FinancialAccountUpdate {
  name?: string;
  account_type?: FinancialAccountType;
  description?: string | null;
  institution_name?: string | null;
  color?: string | null;
  icon?: string | null;
  is_archived?: boolean;
}

export interface BalanceAdjustmentCreate {
  new_balance: string;
  adjustment_date: string;
  description?: string | null;
}

export interface FinancialCategory {
  id: string;
  user_id: string;
  name: string;
  category_type: FinancialCategoryType;
  color?: string | null;
  icon?: string | null;
  is_default: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface FinancialCategoryCreate {
  name: string;
  category_type: FinancialCategoryType;
  color?: string | null;
  icon?: string | null;
}

export interface FinancialCategoryUpdate {
  name?: string;
  color?: string | null;
  icon?: string | null;
  is_archived?: boolean;
}

export interface FinancialTag {
  id: string;
  user_id: string;
  name: string;
  color?: string | null;
  created_at: string;
}

export interface FinancialTagCreate {
  name: string;
  color?: string | null;
}

export interface FinancialTransaction {
  id: string;
  user_id: string;
  account_id: string;
  account_name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  transfer_id?: string | null;
  recurring_rule_id?: string | null;
  transaction_type: FinancialTransactionType;
  amount: string;
  currency: string;
  description: string;
  transaction_date: string;
  merchant_or_source?: string | null;
  notes?: string | null;
  is_voided: boolean;
  voided_at?: string | null;
  tags: FinancialTag[];
  created_at: string;
  updated_at: string;
}

export interface FinancialTransactionCreate {
  account_id: string;
  category_id?: string | null;
  transaction_type: FinancialTransactionType;
  amount: string;
  currency: string;
  description: string;
  transaction_date: string;
  merchant_or_source?: string | null;
  notes?: string | null;
  tag_ids?: string[];
}

export interface FinancialTransactionUpdate {
  account_id?: string;
  category_id?: string | null;
  amount?: string;
  currency?: string;
  description?: string;
  transaction_date?: string;
  merchant_or_source?: string | null;
  notes?: string | null;
  tag_ids?: string[];
}

export interface TransactionListResponse {
  items: FinancialTransaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FinancialTransferCreate {
  source_account_id: string;
  destination_account_id: string;
  amount: string;
  transfer_date: string;
  description?: string | null;
  notes?: string | null;
}

export interface FinancialTransfer {
  id: string;
  user_id: string;
  source_account_id: string;
  source_account_name?: string | null;
  destination_account_id: string;
  destination_account_name?: string | null;
  amount: string;
  currency: string;
  transfer_date: string;
  description?: string | null;
  notes?: string | null;
  is_voided: boolean;
  created_at: string;
  updated_at: string;
}

export interface Budget {
  id: string;
  user_id: string;
  name: string;
  category_id?: string | null;
  category_name?: string | null;
  amount: string;
  currency: string;
  year: number;
  month: number;
  actual_spending: string;
  remaining_amount: string;
  utilization_percentage: number;
  is_overspent: boolean;
  overspent_amount: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface BudgetCreate {
  name: string;
  category_id?: string | null;
  amount: string;
  currency: string;
  year: number;
  month: number;
}

export interface BudgetUpdate {
  name?: string;
  amount?: string;
  category_id?: string | null;
  is_archived?: boolean;
}

export interface RecurringTransaction {
  id: string;
  user_id: string;
  account_id: string;
  account_name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  transaction_type: FinancialTransactionType;
  amount: string;
  currency: string;
  description: string;
  merchant_or_source?: string | null;
  frequency: RecurringFrequency;
  start_date: string;
  end_date?: string | null;
  next_occurrence: string;
  last_generated_occurrence?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecurringTransactionCreate {
  account_id: string;
  category_id?: string | null;
  transaction_type: FinancialTransactionType;
  amount: string;
  currency: string;
  description: string;
  merchant_or_source?: string | null;
  frequency: RecurringFrequency;
  start_date: string;
  end_date?: string | null;
}

export interface RecurringTransactionUpdate {
  account_id?: string;
  category_id?: string | null;
  amount?: string;
  description?: string;
  merchant_or_source?: string | null;
  frequency?: RecurringFrequency;
  end_date?: string | null;
  is_active?: boolean;
}

export interface SavingsGoalEntry {
  id: string;
  savings_goal_id: string;
  user_id: string;
  account_id?: string | null;
  entry_type: 'DEPOSIT' | 'WITHDRAWAL';
  amount: string;
  entry_date: string;
  notes?: string | null;
  created_at: string;
}

export interface SavingsGoalEntryCreate {
  entry_type: 'DEPOSIT' | 'WITHDRAWAL';
  amount: string;
  account_id?: string | null;
  entry_date: string;
  notes?: string | null;
}

export interface FinancialSavingsGoal {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  target_amount: string;
  currency: string;
  target_date?: string | null;
  productivity_goal_id?: string | null;
  productivity_goal_title?: string | null;
  current_amount: string;
  remaining_amount: string;
  progress_percentage: number;
  status: SavingsGoalStatus;
  entries: SavingsGoalEntry[];
  created_at: string;
  updated_at: string;
}

export interface FinancialSavingsGoalCreate {
  title: string;
  description?: string | null;
  target_amount: string;
  currency: string;
  target_date?: string | null;
  productivity_goal_id?: string | null;
}

export interface FinancialSavingsGoalUpdate {
  title?: string;
  description?: string | null;
  target_amount?: string;
  target_date?: string | null;
  productivity_goal_id?: string | null;
  status?: SavingsGoalStatus;
}

export interface CurrencySummary {
  currency: string;
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
  income_this_month: string;
  expense_this_month: string;
  net_cash_flow_this_month: string;
}

export interface FinanceDashboardOverview {
  currencies: CurrencySummary[];
  accounts: FinancialAccount[];
  recent_transactions: FinancialTransaction[];
  active_budgets: Budget[];
  active_savings_goals: FinancialSavingsGoal[];
}

export interface CashFlowPoint {
  period: string;
  income: string;
  expense: string;
  net: string;
}

export interface CategorySpendingItem {
  category_id?: string | null;
  category_name: string;
  color?: string | null;
  total_amount: string;
  percentage: number;
  transaction_count: number;
}

export interface FinancialAnalyticsResponse {
  currency: string;
  cash_flow_trend: CashFlowPoint[];
  category_breakdown: CategorySpendingItem[];
  total_income: string;
  total_expense: string;
  net_cash_flow: string;
  average_transaction_amount: string;
  largest_expenses: FinancialTransaction[];
}
