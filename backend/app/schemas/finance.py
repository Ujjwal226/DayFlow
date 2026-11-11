import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.finance import (
    FinancialAccountType,
    FinancialCategoryType,
    FinancialTransactionType,
    RecurringFrequency,
    SavingsGoalStatus,
)


# --- Financial Accounts ---

class FinancialAccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: FinancialAccountType = FinancialAccountType.BANK_ACCOUNT
    currency: str = Field(..., min_length=3, max_length=3)
    opening_balance: Decimal = Field(default=Decimal("0.00"))
    description: Optional[str] = None
    institution_name: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)


class FinancialAccountCreate(FinancialAccountBase):
    pass


class FinancialAccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    institution_name: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_archived: Optional[bool] = None


class BalanceAdjustmentCreate(BaseModel):
    new_balance: Decimal = Field(...)
    adjustment_date: date = Field(default_factory=date.today)
    description: Optional[str] = Field(None, max_length=255)


class FinancialAccountResponse(FinancialAccountBase):
    id: uuid.UUID
    user_id: uuid.UUID
    calculated_balance: Decimal
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Categories & Tags ---

class FinancialCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category_type: FinancialCategoryType
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)


class FinancialCategoryCreate(FinancialCategoryBase):
    pass


class FinancialCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_archived: Optional[bool] = None


class FinancialCategoryResponse(FinancialCategoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_default: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)


class FinancialTagCreate(FinancialTagBase):
    pass


class FinancialTagResponse(FinancialTagBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Transactions ---

class FinancialTransactionBase(BaseModel):
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    transaction_type: FinancialTransactionType
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = Field(..., min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=255)
    transaction_date: date
    merchant_or_source: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    tag_ids: Optional[List[uuid.UUID]] = None


class FinancialTransactionCreate(FinancialTransactionBase):
    pass


class FinancialTransactionUpdate(BaseModel):
    account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    transaction_date: Optional[date] = None
    merchant_or_source: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    tag_ids: Optional[List[uuid.UUID]] = None


class FinancialTransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    account_name: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None
    transfer_id: Optional[uuid.UUID] = None
    recurring_rule_id: Optional[uuid.UUID] = None
    transaction_type: FinancialTransactionType
    amount: Decimal
    currency: str
    description: str
    transaction_date: date
    merchant_or_source: Optional[str] = None
    notes: Optional[str] = None
    is_voided: bool
    voided_at: Optional[datetime] = None
    tags: List[FinancialTagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: List[FinancialTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Transfers ---

class FinancialTransferCreate(BaseModel):
    source_account_id: uuid.UUID
    destination_account_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    transfer_date: date = Field(default_factory=date.today)
    description: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class FinancialTransferResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_account_id: uuid.UUID
    source_account_name: Optional[str] = None
    destination_account_id: uuid.UUID
    destination_account_name: Optional[str] = None
    amount: Decimal
    currency: str
    transfer_date: date
    description: Optional[str] = None
    notes: Optional[str] = None
    is_voided: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Budgets ---

class BudgetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category_id: Optional[uuid.UUID] = None
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = Field(..., min_length=3, max_length=3)
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    category_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None


class BudgetResponse(BudgetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    category_name: Optional[str] = None
    actual_spending: Decimal
    remaining_amount: Decimal
    utilization_percentage: float
    is_overspent: bool
    overspent_amount: Decimal
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Recurring Transactions ---

class RecurringTransactionBase(BaseModel):
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    transaction_type: FinancialTransactionType
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = Field(..., min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=255)
    merchant_or_source: Optional[str] = Field(None, max_length=100)
    frequency: RecurringFrequency = RecurringFrequency.MONTHLY
    start_date: date
    end_date: Optional[date] = None


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(BaseModel):
    account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    merchant_or_source: Optional[str] = Field(None, max_length=100)
    frequency: Optional[RecurringFrequency] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class RecurringTransactionResponse(RecurringTransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    account_name: Optional[str] = None
    category_name: Optional[str] = None
    next_occurrence: date
    last_generated_occurrence: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Savings Goals ---

class FinancialSavingsGoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    target_amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = Field(..., min_length=3, max_length=3)
    target_date: Optional[date] = None
    productivity_goal_id: Optional[uuid.UUID] = None


class FinancialSavingsGoalCreate(FinancialSavingsGoalBase):
    pass


class FinancialSavingsGoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    target_amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    target_date: Optional[date] = None
    productivity_goal_id: Optional[uuid.UUID] = None
    status: Optional[SavingsGoalStatus] = None


class SavingsGoalEntryCreate(BaseModel):
    entry_type: str = Field(..., pattern="^(DEPOSIT|WITHDRAWAL)$")
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    account_id: Optional[uuid.UUID] = None
    entry_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None


class SavingsGoalEntryResponse(BaseModel):
    id: uuid.UUID
    savings_goal_id: uuid.UUID
    user_id: uuid.UUID
    account_id: Optional[uuid.UUID] = None
    entry_type: str
    amount: Decimal
    entry_date: date
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialSavingsGoalResponse(FinancialSavingsGoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    current_amount: Decimal
    remaining_amount: Decimal
    progress_percentage: float
    status: SavingsGoalStatus
    productivity_goal_title: Optional[str] = None
    entries: List[SavingsGoalEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Financial Analytics & Overview ---

class CurrencySummary(BaseModel):
    currency: str
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    income_this_month: Decimal
    expense_this_month: Decimal
    net_cash_flow_this_month: Decimal


class FinanceDashboardOverview(BaseModel):
    currencies: List[CurrencySummary]
    accounts: List[FinancialAccountResponse]
    recent_transactions: List[FinancialTransactionResponse]
    active_budgets: List[BudgetResponse]
    active_savings_goals: List[FinancialSavingsGoalResponse]


class CashFlowPoint(BaseModel):
    period: str
    income: Decimal
    expense: Decimal
    net: Decimal


class CategorySpendingItem(BaseModel):
    category_id: Optional[uuid.UUID] = None
    category_name: str
    color: Optional[str] = None
    total_amount: Decimal
    percentage: float
    transaction_count: int


class FinancialAnalyticsResponse(BaseModel):
    currency: str
    cash_flow_trend: List[CashFlowPoint]
    category_breakdown: List[CategorySpendingItem]
    total_income: Decimal
    total_expense: Decimal
    net_cash_flow: Decimal
    average_transaction_amount: Decimal
    largest_expenses: List[FinancialTransactionResponse]
