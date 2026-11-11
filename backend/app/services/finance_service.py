import csv
import io
import uuid
import calendar
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.finance import (
    FinancialAccount,
    FinancialCategory,
    FinancialTag,
    FinancialTransaction,
    FinancialTransfer,
    Budget,
    RecurringFinancialTransaction,
    FinancialSavingsGoal,
    FinancialSavingsGoalEntry,
    SavingsGoalStatus,
)
from app.repositories.finance_repository import FinanceRepository
from app.schemas.finance import (
    FinancialAccountCreate,
    FinancialAccountUpdate,
    FinancialAccountResponse,
    BalanceAdjustmentCreate,
    FinancialCategoryCreate,
    FinancialCategoryUpdate,
    FinancialCategoryResponse,
    FinancialTagCreate,
    FinancialTagResponse,
    FinancialTransactionCreate,
    FinancialTransactionUpdate,
    FinancialTransactionResponse,
    TransactionListResponse,
    FinancialTransferCreate,
    FinancialTransferResponse,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionResponse,
    FinancialSavingsGoalCreate,
    FinancialSavingsGoalUpdate,
    FinancialSavingsGoalResponse,
    SavingsGoalEntryCreate,
    SavingsGoalEntryResponse,
    FinanceDashboardOverview,
    CurrencySummary,
    FinancialAnalyticsResponse,
    CashFlowPoint,
    CategorySpendingItem,
)


def advance_next_occurrence(
    current_occurrence: date,
    frequency: str,
    interval: int = 1,
    anchor_day: Optional[int] = None,
) -> date:
    """Safely advances a date according to recurrence rule handling leap years and month ends.
    If anchor_day is provided (typically rule.start_date.day), preserves original month day
    across months with fewer days and restores it when possible (e.g., Feb 29 -> Feb 28 -> Feb 29, or day 31).
    """
    year = current_occurrence.year
    month = current_occurrence.month
    target_day = anchor_day if anchor_day is not None else current_occurrence.day

    if frequency == "DAILY":
        return current_occurrence + timedelta(days=interval)
    elif frequency == "WEEKLY":
        return current_occurrence + timedelta(weeks=interval)
    elif frequency == "MONTHLY":
        total_months = month - 1 + interval
        new_year = year + (total_months // 12)
        new_month = (total_months % 12) + 1
        _, max_days = calendar.monthrange(new_year, new_month)
        new_day = min(target_day, max_days)
        return date(new_year, new_month, new_day)
    elif frequency == "YEARLY":
        new_year = year + interval
        _, max_days = calendar.monthrange(new_year, month)
        new_day = min(target_day, max_days)
        return date(new_year, month, new_day)
    return current_occurrence + timedelta(days=interval)


def sanitize_csv_cell(value: Any) -> str:
    """Formula injection protection: strip or prefix dangerous characters (=, +, -, @, \t, \r)."""
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


class FinanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FinanceRepository(db)

    # ------------------ Accounts ------------------
    def get_accounts(self, user_id: uuid.UUID, include_archived: bool = False) -> List[FinancialAccountResponse]:
        accounts = self.repo.get_accounts_by_user(user_id, include_archived)
        res = []
        for acc in accounts:
            bal = self.repo.calculate_account_balance(acc.id, user_id)
            res.append(
                FinancialAccountResponse(
                    id=acc.id,
                    user_id=acc.user_id,
                    name=acc.name,
                    account_type=acc.account_type,
                    currency=acc.currency,
                    opening_balance=acc.opening_balance,
                    calculated_balance=bal,
                    description=acc.description,
                    institution_name=acc.institution_name,
                    color=acc.color,
                    icon=acc.icon,
                    is_archived=acc.is_archived,
                    created_at=acc.created_at,
                    updated_at=acc.updated_at,
                )
            )
        return res

    def get_account(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialAccountResponse]:
        acc = self.repo.get_account_by_id(account_id, user_id)
        if not acc:
            return None
        bal = self.repo.calculate_account_balance(acc.id, user_id)
        return FinancialAccountResponse(
            id=acc.id,
            user_id=acc.user_id,
            name=acc.name,
            account_type=acc.account_type,
            currency=acc.currency,
            opening_balance=acc.opening_balance,
            calculated_balance=bal,
            description=acc.description,
            institution_name=acc.institution_name,
            color=acc.color,
            icon=acc.icon,
            is_archived=acc.is_archived,
            created_at=acc.created_at,
            updated_at=acc.updated_at,
        )

    def create_account(self, user_id: uuid.UUID, data: FinancialAccountCreate) -> FinancialAccountResponse:
        self.repo.seed_default_categories(user_id)
        acc = self.repo.create_account(user_id, data)
        return self.get_account(acc.id, user_id) # type: ignore

    def update_account(self, account_id: uuid.UUID, user_id: uuid.UUID, data: FinancialAccountUpdate) -> Optional[FinancialAccountResponse]:
        acc = self.repo.get_account_by_id(account_id, user_id)
        if not acc:
            return None
        self.repo.update_account(acc, data)
        return self.get_account(acc.id, user_id)

    def archive_account(self, account_id: uuid.UUID, user_id: uuid.UUID, archive: bool = True) -> Optional[FinancialAccountResponse]:
        acc = self.repo.get_account_by_id(account_id, user_id)
        if not acc:
            return None
        acc.is_archived = archive
        self.db.commit()
        return self.get_account(acc.id, user_id)

    def create_balance_adjustment(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        data: BalanceAdjustmentCreate
    ) -> FinancialAccountResponse:
        acc = self.repo.get_account_by_id(account_id, user_id)
        if not acc:
            raise ValueError("Account not found")

        current = self.repo.calculate_account_balance(account_id, user_id)
        delta = data.new_balance - current

        if delta != Decimal("0.00"):
            adj_tx = FinancialTransaction(
                user_id=user_id,
                account_id=account_id,
                transaction_type="ADJUSTMENT",
                amount=delta,
                currency=acc.currency,
                transaction_date=data.adjustment_date,
                description=f"Balance Adjustment ({'increase' if delta > 0 else 'decrease'})",
                notes=data.description or f"Manual balance reconciliation from {current} to {data.new_balance}",
                is_voided=False,
            )
            self.db.add(adj_tx)
            self.db.commit()

        return self.get_account(account_id, user_id) # type: ignore

    # ------------------ Categories & Tags ------------------
    def get_categories(self, user_id: uuid.UUID) -> List[FinancialCategoryResponse]:
        cats = self.repo.get_categories_by_user(user_id)
        if not cats:
            cats = self.repo.seed_default_categories(user_id)
        return [FinancialCategoryResponse.model_validate(c) for c in cats]

    def create_category(self, user_id: uuid.UUID, data: FinancialCategoryCreate) -> FinancialCategoryResponse:
        cat = self.repo.create_category(user_id, data)
        return FinancialCategoryResponse.model_validate(cat)

    def update_category(self, category_id: uuid.UUID, user_id: uuid.UUID, data: FinancialCategoryUpdate) -> Optional[FinancialCategoryResponse]:
        cat = self.repo.get_category_by_id(category_id, user_id)
        if not cat:
            return None
        updated = self.repo.update_category(cat, data)
        return FinancialCategoryResponse.model_validate(updated)

    def delete_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        cat = self.repo.get_category_by_id(category_id, user_id)
        if not cat:
            return False
        self.repo.delete_category(cat)
        return True

    def get_tags(self, user_id: uuid.UUID) -> List[FinancialTagResponse]:
        tags = self.repo.get_tags_by_user(user_id)
        return [FinancialTagResponse.model_validate(t) for t in tags]

    def create_tag(self, user_id: uuid.UUID, data: FinancialTagCreate) -> FinancialTagResponse:
        tag = self.repo.create_tag(user_id, data)
        return FinancialTagResponse.model_validate(tag)

    def delete_tag(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        tag = self.repo.get_tag_by_id(tag_id, user_id)
        if not tag:
            return False
        self.repo.delete_tag(tag)
        return True

    # ------------------ Transactions ------------------
    def get_transactions(
        self,
        user_id: uuid.UUID,
        account_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        include_voided: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> TransactionListResponse:
        items, total = self.repo.get_transactions_filtered(
            user_id, account_id, category_id, transaction_type,
            start_date, end_date, search, include_voided, page, page_size
        )
        res = []
        for item in items:
            tx_dict = {
                "id": item.id,
                "user_id": item.user_id,
                "account_id": item.account_id,
                "account_name": item.account.name if item.account else None,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "transfer_id": item.transfer_id,
                "recurring_rule_id": item.recurring_rule_id,
                "transaction_type": item.transaction_type,
                "amount": item.amount,
                "currency": item.currency,
                "description": item.description,
                "transaction_date": item.transaction_date,
                "merchant_or_source": item.merchant_or_source,
                "notes": item.notes,
                "is_voided": item.is_voided,
                "voided_at": item.voided_at,
                "tags": [FinancialTagResponse.model_validate(t.tag) for t in item.tag_links if t.tag],
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            res.append(FinancialTransactionResponse(**tx_dict))

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return TransactionListResponse(
            items=res,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def get_transaction(self, tx_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTransactionResponse]:
        item = self.repo.get_transaction_by_id(tx_id, user_id)
        if not item:
            return None
        tx_dict = {
            "id": item.id,
            "user_id": item.user_id,
            "account_id": item.account_id,
            "account_name": item.account.name if item.account else None,
            "category_id": item.category_id,
            "category_name": item.category.name if item.category else None,
            "transfer_id": item.transfer_id,
            "recurring_rule_id": item.recurring_rule_id,
            "transaction_type": item.transaction_type,
            "amount": item.amount,
            "currency": item.currency,
            "description": item.description,
            "transaction_date": item.transaction_date,
            "merchant_or_source": item.merchant_or_source,
            "notes": item.notes,
            "is_voided": item.is_voided,
            "voided_at": item.voided_at,
            "tags": [FinancialTagResponse.model_validate(t.tag) for t in item.tag_links if t.tag],
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        return FinancialTransactionResponse(**tx_dict)

    def create_transaction(
        self,
        user_id: uuid.UUID,
        data: FinancialTransactionCreate
    ) -> FinancialTransactionResponse:
        account = self.repo.get_account_by_id(data.account_id, user_id)
        if not account:
            raise ValueError("Target account not found")

        if data.currency.upper() != account.currency.upper():
            raise ValueError(f"Transaction currency {data.currency} must match account currency {account.currency}")

        tx = self.repo.create_transaction(user_id, data)
        return self.get_transaction(tx.id, user_id) # type: ignore

    def update_transaction(
        self,
        tx_id: uuid.UUID,
        user_id: uuid.UUID,
        data: FinancialTransactionUpdate
    ) -> Optional[FinancialTransactionResponse]:
        tx = self.repo.get_transaction_by_id(tx_id, user_id)
        if not tx:
            return None
        if tx.is_voided:
            raise ValueError("Cannot update a voided transaction")

        updated = self.repo.update_transaction(tx, data)
        return self.get_transaction(updated.id, user_id)

    def void_transaction(self, tx_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTransactionResponse]:
        tx = self.repo.get_transaction_by_id(tx_id, user_id)
        if not tx:
            return None
        if tx.is_voided:
            return self.get_transaction(tx.id, user_id)

        if tx.transfer_id:
            transfer = self.repo.get_transfer_by_id(tx.transfer_id, user_id)
            if transfer:
                self.repo.void_transfer(transfer)
                return self.get_transaction(tx.id, user_id)

        voided = self.repo.void_transaction(tx)
        return self.get_transaction(voided.id, user_id)

    # ------------------ Transfers ------------------
    def create_transfer(self, user_id: uuid.UUID, data: FinancialTransferCreate) -> FinancialTransferResponse:
        if data.source_account_id == data.destination_account_id:
            raise ValueError("Source and destination accounts must be different")

        source = self.repo.get_account_by_id(data.source_account_id, user_id)
        dest = self.repo.get_account_by_id(data.destination_account_id, user_id)

        if not source or not dest:
            raise ValueError("Source or destination account not found")

        if source.currency.upper() != dest.currency.upper():
            raise ValueError(f"Cross-currency transfers are not supported. Source: {source.currency}, Destination: {dest.currency}")

        if source.account_type != "CREDIT_CARD":
            current_bal = self.repo.calculate_account_balance(source.id, user_id)
            if current_bal < data.amount:
                raise ValueError(f"Insufficient funds in source account ({source.currency} {current_bal} available, {data.amount} requested)")

        transfer = self.repo.create_transfer(user_id, data, source.currency)
        return FinancialTransferResponse(
            id=transfer.id,
            user_id=transfer.user_id,
            source_account_id=transfer.source_account_id,
            source_account_name=source.name,
            destination_account_id=transfer.destination_account_id,
            destination_account_name=dest.name,
            amount=transfer.amount,
            currency=transfer.currency,
            transfer_date=transfer.transfer_date,
            description=transfer.description,
            notes=transfer.notes,
            is_voided=transfer.is_voided,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        )

    def void_transfer(self, transfer_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTransferResponse]:
        transfer = self.repo.get_transfer_by_id(transfer_id, user_id)
        if not transfer:
            return None
        voided = self.repo.void_transfer(transfer)
        source = self.repo.get_account_by_id(voided.source_account_id, user_id)
        dest = self.repo.get_account_by_id(voided.destination_account_id, user_id)
        return FinancialTransferResponse(
            id=voided.id,
            user_id=voided.user_id,
            source_account_id=voided.source_account_id,
            source_account_name=source.name if source else None,
            destination_account_id=voided.destination_account_id,
            destination_account_name=dest.name if dest else None,
            amount=voided.amount,
            currency=voided.currency,
            transfer_date=voided.transfer_date,
            description=voided.description,
            notes=voided.notes,
            is_voided=voided.is_voided,
            created_at=voided.created_at,
            updated_at=voided.updated_at,
        )

    # ------------------ Budgets ------------------
    def get_budgets(self, user_id: uuid.UUID, year: int, month: int) -> List[BudgetResponse]:
        budgets = self.repo.get_budgets_by_month(user_id, year, month)
        res = []
        for b in budgets:
            spent = self.repo.calculate_budget_spent(b)
            remaining = b.amount - spent
            pct = round((spent / b.amount) * 100, 2) if b.amount > 0 else Decimal("0.00")
            overspent = spent > b.amount
            overspent_amt = (spent - b.amount) if overspent else Decimal("0.00")

            res.append(
                BudgetResponse(
                    id=b.id,
                    user_id=b.user_id,
                    name=b.name,
                    category_id=b.category_id,
                    category_name=b.category.name if b.category else "Overall",
                    amount=b.amount,
                    currency=b.currency,
                    year=b.year,
                    month=b.month,
                    actual_spending=spent,
                    remaining_amount=remaining,
                    utilization_percentage=float(pct),
                    is_overspent=overspent,
                    overspent_amount=overspent_amt,
                    is_archived=b.is_archived,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                )
            )
        return res

    def create_budget(self, user_id: uuid.UUID, data: BudgetCreate) -> BudgetResponse:
        budget = self.repo.create_budget(user_id, data)
        spent = self.repo.calculate_budget_spent(budget)
        remaining = budget.amount - spent
        pct = round((spent / budget.amount) * 100, 2) if budget.amount > 0 else Decimal("0.00")
        overspent = spent > budget.amount
        overspent_amt = (spent - budget.amount) if overspent else Decimal("0.00")

        return BudgetResponse(
            id=budget.id,
            user_id=budget.user_id,
            name=budget.name,
            category_id=budget.category_id,
            category_name=budget.category.name if budget.category else "Overall",
            amount=budget.amount,
            currency=budget.currency,
            year=budget.year,
            month=budget.month,
            actual_spending=spent,
            remaining_amount=remaining,
            utilization_percentage=float(pct),
            is_overspent=overspent,
            overspent_amount=overspent_amt,
            is_archived=budget.is_archived,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )

    def update_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID, data: BudgetUpdate) -> Optional[BudgetResponse]:
        b = self.repo.get_budget_by_id(budget_id, user_id)
        if not b:
            return None
        updated = self.repo.update_budget(b, data)
        spent = self.repo.calculate_budget_spent(updated)
        remaining = updated.amount - spent
        pct = round((spent / updated.amount) * 100, 2) if updated.amount > 0 else Decimal("0.00")
        overspent = spent > updated.amount
        overspent_amt = (spent - updated.amount) if overspent else Decimal("0.00")

        return BudgetResponse(
            id=updated.id,
            user_id=updated.user_id,
            name=updated.name,
            category_id=updated.category_id,
            category_name=updated.category.name if updated.category else "Overall",
            amount=updated.amount,
            currency=updated.currency,
            year=updated.year,
            month=updated.month,
            actual_spending=spent,
            remaining_amount=remaining,
            utilization_percentage=float(pct),
            is_overspent=overspent,
            overspent_amount=overspent_amt,
            is_archived=updated.is_archived,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    def delete_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        b = self.repo.get_budget_by_id(budget_id, user_id)
        if not b:
            return False
        self.repo.delete_budget(b)
        return True

    # ------------------ Recurring Transactions ------------------
    def get_recurring_rules(self, user_id: uuid.UUID) -> List[RecurringTransactionResponse]:
        rules = self.repo.get_recurring_rules_by_user(user_id)
        res = []
        for r in rules:
            res.append(
                RecurringTransactionResponse(
                    id=r.id,
                    user_id=r.user_id,
                    account_id=r.account_id,
                    account_name=r.account.name if r.account else None,
                    category_id=r.category_id,
                    category_name=r.category.name if r.category else None,
                    transaction_type=r.transaction_type,
                    amount=r.amount,
                    currency=r.currency,
                    description=r.description,
                    merchant_or_source=r.merchant_or_source,
                    frequency=r.frequency,
                    start_date=r.start_date,
                    end_date=r.end_date,
                    next_occurrence=r.next_occurrence,
                    last_generated_occurrence=r.last_generated_occurrence,
                    is_active=r.is_active,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )
        return res

    def create_recurring_rule(self, user_id: uuid.UUID, data: RecurringTransactionCreate) -> RecurringTransactionResponse:
        account = self.repo.get_account_by_id(data.account_id, user_id)
        if not account:
            raise ValueError("Target account not found")

        rule = self.repo.create_recurring_rule(user_id, data)
        return RecurringTransactionResponse(
            id=rule.id,
            user_id=rule.user_id,
            account_id=rule.account_id,
            account_name=rule.account.name if rule.account else None,
            category_id=rule.category_id,
            category_name=rule.category.name if rule.category else None,
            transaction_type=rule.transaction_type,
            amount=rule.amount,
            currency=rule.currency,
            description=rule.description,
            merchant_or_source=rule.merchant_or_source,
            frequency=rule.frequency,
            start_date=rule.start_date,
            end_date=rule.end_date,
            next_occurrence=rule.next_occurrence,
            last_generated_occurrence=rule.last_generated_occurrence,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def update_recurring_rule(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        data: RecurringTransactionUpdate
    ) -> Optional[RecurringTransactionResponse]:
        rule = self.repo.get_recurring_by_id(rule_id, user_id)
        if not rule:
            return None
        updated = self.repo.update_recurring_rule(rule, data)
        return RecurringTransactionResponse(
            id=updated.id,
            user_id=updated.user_id,
            account_id=updated.account_id,
            account_name=updated.account.name if updated.account else None,
            category_id=updated.category_id,
            category_name=updated.category.name if updated.category else None,
            transaction_type=updated.transaction_type,
            amount=updated.amount,
            currency=updated.currency,
            description=updated.description,
            merchant_or_source=updated.merchant_or_source,
            frequency=updated.frequency,
            start_date=updated.start_date,
            end_date=updated.end_date,
            next_occurrence=updated.next_occurrence,
            last_generated_occurrence=updated.last_generated_occurrence,
            is_active=updated.is_active,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    def delete_recurring_rule(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        rule = self.repo.get_recurring_by_id(rule_id, user_id)
        if not rule:
            return False
        self.repo.delete_recurring_rule(rule)
        return True

    def process_due_recurring_transactions(self, as_of_date: Optional[date] = None) -> int:
        target_date = as_of_date or date.today()
        due_rules = self.repo.get_due_recurring_rules(target_date)
        processed_count = 0

        for rule in due_rules:
            occ_date = rule.next_occurrence
            if not self.repo.has_occurrence_record(rule.id, occ_date):
                tx_data = FinancialTransactionCreate(
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    transaction_type=rule.transaction_type,
                    amount=rule.amount,
                    currency=rule.currency,
                    transaction_date=occ_date,
                    description=rule.description,
                    merchant_or_source=rule.merchant_or_source,
                    notes=f"Auto-generated recurring transaction: {rule.description}",
                )
                tx = self.repo.create_transaction(rule.user_id, tx_data)
                self.repo.record_recurring_occurrence(rule.id, occ_date, tx.id)
                rule.last_generated_occurrence = occ_date
                processed_count += 1

            anchor_day = rule.start_date.day if rule.start_date else None
            next_occ = advance_next_occurrence(occ_date, rule.frequency, anchor_day=anchor_day)
            if rule.end_date and next_occ > rule.end_date:
                rule.is_active = False
            rule.next_occurrence = next_occ
            self.db.commit()

        return processed_count

    # ------------------ Savings Goals ------------------
    def get_savings_goals(self, user_id: uuid.UUID) -> List[FinancialSavingsGoalResponse]:
        goals = self.repo.get_savings_goals_by_user(user_id)
        res = []
        for g in goals:
            curr = self.repo.calculate_savings_goal_current(g.id)
            rem = max(Decimal("0.00"), g.target_amount - curr)
            pct = round((curr / g.target_amount) * 100, 2) if g.target_amount > 0 else Decimal("0.00")
            entries_res = [
                SavingsGoalEntryResponse(
                    id=e.id,
                    savings_goal_id=e.savings_goal_id,
                    user_id=e.user_id,
                    account_id=e.account_id,
                    entry_type=e.entry_type,
                    amount=e.amount,
                    entry_date=e.entry_date,
                    notes=e.notes,
                    created_at=e.created_at,
                )
                for e in g.entries
            ]
            res.append(
                FinancialSavingsGoalResponse(
                    id=g.id,
                    user_id=g.user_id,
                    title=g.title,
                    description=g.description,
                    target_amount=g.target_amount,
                    currency=g.currency,
                    target_date=g.target_date,
                    productivity_goal_id=g.productivity_goal_id,
                    current_amount=curr,
                    remaining_amount=rem,
                    progress_percentage=float(pct),
                    status=g.status,
                    productivity_goal_title=g.productivity_goal.title if g.productivity_goal else None,
                    entries=entries_res,
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                )
            )
        return res

    def get_savings_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialSavingsGoalResponse]:
        g = self.repo.get_savings_goal_by_id(goal_id, user_id)
        if not g:
            return None
        curr = self.repo.calculate_savings_goal_current(g.id)
        rem = max(Decimal("0.00"), g.target_amount - curr)
        pct = round((curr / g.target_amount) * 100, 2) if g.target_amount > 0 else Decimal("0.00")
        entries_res = [
            SavingsGoalEntryResponse(
                id=e.id,
                savings_goal_id=e.savings_goal_id,
                user_id=e.user_id,
                account_id=e.account_id,
                entry_type=e.entry_type,
                amount=e.amount,
                entry_date=e.entry_date,
                notes=e.notes,
                created_at=e.created_at,
            )
            for e in g.entries
        ]
        return FinancialSavingsGoalResponse(
            id=g.id,
            user_id=g.user_id,
            title=g.title,
            description=g.description,
            target_amount=g.target_amount,
            currency=g.currency,
            target_date=g.target_date,
            productivity_goal_id=g.productivity_goal_id,
            current_amount=curr,
            remaining_amount=rem,
            progress_percentage=float(pct),
            status=g.status,
            productivity_goal_title=g.productivity_goal.title if g.productivity_goal else None,
            entries=entries_res,
            created_at=g.created_at,
            updated_at=g.updated_at,
        )

    def create_savings_goal(self, user_id: uuid.UUID, data: FinancialSavingsGoalCreate) -> FinancialSavingsGoalResponse:
        goal = self.repo.create_savings_goal(user_id, data)
        return self.get_savings_goal(goal.id, user_id) # type: ignore

    def update_savings_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID, data: FinancialSavingsGoalUpdate) -> Optional[FinancialSavingsGoalResponse]:
        goal = self.repo.get_savings_goal_by_id(goal_id, user_id)
        if not goal:
            return None
        self.repo.update_savings_goal(goal, data)
        return self.get_savings_goal(goal.id, user_id)

    def delete_savings_goal(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        goal = self.repo.get_savings_goal_by_id(goal_id, user_id)
        if not goal:
            return False
        self.repo.delete_savings_goal(goal)
        return True

    def add_savings_entry(self, user_id: uuid.UUID, goal_id: uuid.UUID, data: SavingsGoalEntryCreate) -> SavingsGoalEntryResponse:
        goal = self.repo.get_savings_goal_by_id(goal_id, user_id)
        if not goal:
            raise ValueError("Savings goal not found")
        if data.entry_type == "WITHDRAWAL":
            current_saved = self.repo.calculate_savings_goal_current(goal_id)
            if data.amount > current_saved:
                raise ValueError(f"Cannot withdraw {goal.currency} {data.amount}: only {goal.currency} {current_saved} available in savings goal")

        entry = self.repo.add_savings_entry(user_id, goal_id, data)
        return SavingsGoalEntryResponse(
            id=entry.id,
            savings_goal_id=entry.savings_goal_id,
            user_id=entry.user_id,
            account_id=entry.account_id,
            entry_type=entry.entry_type,
            amount=entry.amount,
            entry_date=entry.entry_date,
            notes=entry.notes,
            created_at=entry.created_at,
        )

    # ------------------ Overview & Analytics ------------------
    def get_dashboard_overview(self, user_id: uuid.UUID) -> FinanceDashboardOverview:
        accounts = self.repo.get_accounts_by_user(user_id, include_archived=False)
        currencies = list(set(a.currency for a in accounts))
        if not currencies:
            currencies = ["USD"]

        currency_summaries = []
        today = date.today()
        month_start = date(today.year, today.month, 1)
        next_month = date(today.year + (today.month // 12), (today.month % 12) + 1, 1)

        for curr in sorted(currencies):
            curr_accounts = [a for a in accounts if a.currency == curr]
            assets = Decimal("0.00")
            liabilities = Decimal("0.00")

            for acc in curr_accounts:
                bal = self.repo.calculate_account_balance(acc.id, user_id)
                if acc.account_type == "CREDIT_CARD":
                    liabilities += max(Decimal("0.00"), bal)
                else:
                    if bal >= 0:
                        assets += bal
                    else:
                        liabilities += abs(bal)

            txs_month = self.db.query(FinancialTransaction).filter(
                FinancialTransaction.user_id == user_id,
                FinancialTransaction.currency == curr,
                FinancialTransaction.is_voided.is_(False),
                FinancialTransaction.transaction_date >= month_start,
                FinancialTransaction.transaction_date < next_month
            ).all()

            inc = sum((t.amount for t in txs_month if t.transaction_type == "INCOME"), Decimal("0.00"))
            exp = sum((t.amount for t in txs_month if t.transaction_type == "EXPENSE"), Decimal("0.00"))

            currency_summaries.append(
                CurrencySummary(
                    currency=curr,
                    total_assets=assets,
                    total_liabilities=liabilities,
                    net_worth=assets - liabilities,
                    income_this_month=inc,
                    expense_this_month=exp,
                    net_cash_flow_this_month=inc - exp,
                )
            )

        accounts_res = self.get_accounts(user_id, include_archived=False)
        recent_txs = self.get_transactions(user_id, page=1, page_size=10).items
        active_budgets = self.get_budgets(user_id, today.year, today.month)
        active_goals = self.get_savings_goals(user_id)

        return FinanceDashboardOverview(
            currencies=currency_summaries,
            accounts=accounts_res,
            recent_transactions=recent_txs,
            active_budgets=active_budgets,
            active_savings_goals=active_goals,
        )

    def get_financial_analytics(
        self,
        user_id: uuid.UUID,
        currency: str = "USD",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> FinancialAnalyticsResponse:
        currency = currency.upper()
        today = date.today()
        s_date = start_date or (today - timedelta(days=180))
        e_date = end_date or today

        txs = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.currency == currency,
            FinancialTransaction.is_voided.is_(False),
            FinancialTransaction.transaction_date >= s_date,
            FinancialTransaction.transaction_date <= e_date
        ).all()

        total_inc = sum((t.amount for t in txs if t.transaction_type == "INCOME"), Decimal("0.00"))
        total_exp = sum((t.amount for t in txs if t.transaction_type == "EXPENSE"), Decimal("0.00"))
        net_cash_flow = total_inc - total_exp
        avg_amt = (sum((t.amount for t in txs), Decimal("0.00")) / len(txs)) if txs else Decimal("0.00")

        # 6-month cash flow points
        points = []
        for i in range(5, -1, -1):
            target_year = today.year
            target_month = today.month - i
            while target_month <= 0:
                target_month += 12
                target_year -= 1

            p_start = date(target_year, target_month, 1)
            next_m = target_month + 1
            next_y = target_year
            if next_m > 12:
                next_m = 1
                next_y += 1
            p_end = date(next_y, next_m, 1)

            m_txs = [t for t in txs if p_start <= t.transaction_date < p_end]
            m_inc = sum((t.amount for t in m_txs if t.transaction_type == "INCOME"), Decimal("0.00"))
            m_exp = sum((t.amount for t in m_txs if t.transaction_type == "EXPENSE"), Decimal("0.00"))
            points.append(
                CashFlowPoint(
                    period=f"{target_year}-{str(target_month).zfill(2)}",
                    income=m_inc,
                    expense=m_exp,
                    net=m_inc - m_exp,
                )
            )

        # Category spending breakdown
        exp_txs = [t for t in txs if t.transaction_type == "EXPENSE"]
        cat_map: Dict[Optional[uuid.UUID], Tuple[str, Optional[str], Decimal, int]] = {}
        for t in exp_txs:
            cid = t.category_id
            cname = t.category.name if t.category else "Uncategorized"
            ccolor = t.category.color if t.category else "#6B7280"
            if cid not in cat_map:
                cat_map[cid] = (cname, ccolor, Decimal("0.00"), 0)
            cname, ccolor, cur_amt, cur_cnt = cat_map[cid]
            cat_map[cid] = (cname, ccolor, cur_amt + t.amount, cur_cnt + 1)

        category_breakdown = []
        for cid, (name, color, amt, cnt) in sorted(cat_map.items(), key=lambda x: x[1][2], reverse=True):
            pct = round((amt / total_exp) * 100, 2) if total_exp > 0 else Decimal("0.00")
            category_breakdown.append(
                CategorySpendingItem(
                    category_id=cid,
                    category_name=name,
                    color=color,
                    total_amount=amt,
                    percentage=float(pct),
                    transaction_count=cnt,
                )
            )

        largest = sorted(exp_txs, key=lambda x: x.amount, reverse=True)[:5]
        largest_res = [self.get_transaction(t.id, user_id) for t in largest if t] # type: ignore

        return FinancialAnalyticsResponse(
            currency=currency,
            cash_flow_trend=points,
            category_breakdown=category_breakdown,
            total_income=total_inc,
            total_expense=total_exp,
            net_cash_flow=net_cash_flow,
            average_transaction_amount=avg_amt,
            largest_expenses=[t for t in largest_res if t is not None],
        )

    # ------------------ CSV Exports ------------------
    def export_transactions_csv(
        self,
        user_id: uuid.UUID,
        account_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_voided: bool = True,
    ) -> str:
        txs, _ = self.repo.get_transactions_filtered(
            user_id, account_id, category_id, transaction_type,
            start_date, end_date, None, include_voided, page=1, page_size=100000
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Date", "Type", "Amount", "Currency", "Account", "Category",
            "Description", "Merchant", "Notes", "Status"
        ])

        for tx in txs:
            writer.writerow([
                sanitize_csv_cell(str(tx.id)),
                sanitize_csv_cell(tx.transaction_date.isoformat()),
                sanitize_csv_cell(tx.transaction_type),
                sanitize_csv_cell(str(tx.amount)),
                sanitize_csv_cell(tx.currency),
                sanitize_csv_cell(tx.account.name if tx.account else ""),
                sanitize_csv_cell(tx.category.name if tx.category else ""),
                sanitize_csv_cell(tx.description),
                sanitize_csv_cell(tx.merchant_or_source or ""),
                sanitize_csv_cell(tx.notes or ""),
                sanitize_csv_cell("VOIDED" if tx.is_voided else "ACTIVE"),
            ])

        return output.getvalue()
