# DayFlow — Personal Finance Management Documentation

## 1. Overview
Stage 4 of DayFlow introduces a production-ready, multi-user **Personal Finance Management Platform** seamlessly integrated with the DayFlow productivity suite (Tasks, Projects, Dashboard, Goals, and Notifications).

The module adheres to core financial principles:
1. **Mathematical Precision**: Python `Decimal` and PostgreSQL `NUMERIC(14, 2)` are strictly used for all calculations, balances, ledger entries, and aggregations. Floating-point arithmetic is never used for authoritative ledger operations.
2. **Multi-Currency Separation**: Accounts, transactions, and budgets preserve explicit currency codes (e.g., `USD`, `EUR`, `GBP`). Net worth, monthly cash flow, and budgets are grouped strictly by currency. Mixed-currency arithmetic without explicit conversion is rejected.
3. **Atomic Transfers**: Transfers are atomic double-entry operations between a source and destination account owned by the same user. Paired ledger records are generated atomically; voiding a transfer automatically voids both legs and restores account balances. Cross-currency transfers without explicit exchange rate conversion are rejected.
4. **Idempotent Recurring Transactions**: Recurring rules run on schedules (daily, weekly, monthly, yearly) using safe calendar arithmetic (month-end clamping and leap-year safety). Occurrences are logged in `recurring_financial_occurrence_records` with unique constraints `(recurring_rule_id, occurrence_date)` to prevent duplicate transactions.
5. **Budget Alerts**: Thresholds (75%, 90%, 100%) evaluate monthly actual spending against budgeted ceilings. System notifications and emails are dispatched respecting user quiet hours and delivery preferences with deduplication flags (`alert_75_sent`, `alert_90_sent`, `alert_100_sent`).
6. **Savings Goals & Milestones**: Dedicated targets with deposit and withdrawal ledger entries. Goals can optionally link to Stage 3G Productivity Goals for long-term financial planning.
7. **CSV Export & Security**: Transaction and account CSV exports feature formula injection mitigation (stripping or quoting leading `=`, `+`, `-`, `@`).

---

## 2. Architecture & Data Model

### Database Tables (Alembic Head: `e5f6a7b8c9d0`)
- `financial_accounts`: User-owned accounts (`CASH`, `BANK_ACCOUNT`, `SAVINGS_ACCOUNT`, `CREDIT_CARD`, `DIGITAL_WALLET`, `CUSTOM`). Tracks opening balance and soft archiving.
- `financial_categories`: User-owned categories (`INCOME`, `EXPENSE`), pre-seeded with sensible defaults upon first access.
- `financial_tags` & `financial_transaction_tags`: Many-to-many transaction tagging.
- `financial_transfers`: Audit records of inter-account fund transfers with debit/credit paired transactions.
- `financial_transactions`: Authoritative ledger rows for `INCOME`, `EXPENSE`, `TRANSFER`, and `ADJUSTMENT`.
- `financial_budgets`: Category or overall monthly budget allocations.
- `recurring_financial_transactions`: Scheduled recurrence rules.
- `recurring_financial_occurrence_records`: Idempotent execution log for recurring rules.
- `financial_savings_goals` & `financial_savings_goal_entries`: Target amounts, target dates, and auditable deposit/withdrawal entries.

---

## 3. API Endpoints

All endpoints are mounted under `/api/v1/finance` and protected by JWT authentication.

### Accounts
- `GET /api/v1/finance/accounts` — List active (or archived) accounts with calculated live balances.
- `POST /api/v1/finance/accounts` — Create an account.
- `GET /api/v1/finance/accounts/{id}` — Fetch specific account details.
- `PUT /api/v1/finance/accounts/{id}` — Update account information.
- `PATCH /api/v1/finance/accounts/{id}/archive` — Archive or restore an account.
- `POST /api/v1/finance/accounts/{id}/adjust-balance` — Reconcile and adjust ledger balance.

### Transactions & Transfers
- `GET /api/v1/finance/transactions` — Paginated and filtered transaction search (by account, category, type, date range, search query, void status).
- `POST /api/v1/finance/transactions` — Record income or expense ledger entry.
- `GET /api/v1/finance/transactions/{id}` — Retrieve transaction details.
- `PUT /api/v1/finance/transactions/{id}` — Update non-voided transaction.
- `POST /api/v1/finance/transactions/{id}/void` — Void transaction and reverse balance impact.
- `POST /api/v1/finance/transfers` — Create atomic transfer between accounts.
- `POST /api/v1/finance/transfers/{id}/void` — Void transfer and reverse paired legs.

### Categories & Tags
- `GET /api/v1/finance/categories` — List categories (seeds defaults if first access).
- `POST /api/v1/finance/categories` — Create custom category.
- `PUT /api/v1/finance/categories/{id}` — Update category.
- `DELETE /api/v1/finance/categories/{id}` — Delete category.
- `GET /api/v1/finance/tags` — List custom tags.
- `POST /api/v1/finance/tags` — Create tag.
- `DELETE /api/v1/finance/tags/{id}` — Delete tag.

### Budgets & Recurring
- `GET /api/v1/finance/budgets` — List monthly budgets with actual spending, remaining amounts, and utilization percentages.
- `POST /api/v1/finance/budgets` — Set new budget ceiling.
- `PUT /api/v1/finance/budgets/{id}` — Update budget.
- `DELETE /api/v1/finance/budgets/{id}` — Delete budget.
- `GET /api/v1/finance/recurring` — List recurring rules.
- `POST /api/v1/finance/recurring` — Set up recurring transaction schedule.
- `PUT /api/v1/finance/recurring/{id}` — Update schedule.
- `DELETE /api/v1/finance/recurring/{id}` — Delete schedule.

### Savings Goals
- `GET /api/v1/finance/savings-goals` — List active savings goals.
- `POST /api/v1/finance/savings-goals` — Create savings goal.
- `GET /api/v1/finance/savings-goals/{id}` — Get goal with contribution ledger history.
- `PUT /api/v1/finance/savings-goals/{id}` — Update goal.
- `DELETE /api/v1/finance/savings-goals/{id}` — Delete goal.
- `POST /api/v1/finance/savings-goals/{id}/entries` — Record deposit contribution or withdrawal.

### Analytics & CSV Export
- `GET /api/v1/finance/overview` — Multi-currency net worth, cash flow, accounts, and recent transactions.
- `GET /api/v1/finance/analytics` — Cash flow trends (6-month period), category spending breakdown, largest expenses.
- `GET /api/v1/finance/export/csv` — CSV export with injection mitigation.

---

## 4. Frontend Experience
- **Dedicated Route**: `/finance` added to app routing and top dashboard navigation.
- **Unified Tabs**: Overview, Accounts, Transactions, Budgets, and Savings Goals.
- **Interactive Modals**: Account Creation, Balance Adjustment, Transaction Entry, Inter-Account Transfer, Budget Planning, and Savings Contribution.
- **Dashboard Widgets**:
  - `FinanceNetWorthWidget` (`finance_net_worth`): Net worth and asset/liability ratio.
  - `FinanceCashFlowWidget` (`finance_cash_flow`): Current month cash flow with income and expense tracking.
  - Registered in `WIDGET_REGISTRY`.

---

## 5. Test Verification
- **Backend Tests (`backend/tests/test_finance.py`)**: 10 tests passing covering account balance calculations, ledger operations, void reversals, atomic transfers, cross-currency rejection, budget calculations, savings goal progress, analytics, CSV exports, and multi-user isolation. Full backend suite: **187 passing tests**.
- **Frontend Tests (`frontend/src/test/financePage.test.tsx` & `dashboardRegistry.test.ts`)**: Full vitest suite: **118 passing tests**.
- **Code Quality**: Clean TypeScript build (`tsc -b`), clean Vite production bundle, clean ESLint (`0 errors`).
