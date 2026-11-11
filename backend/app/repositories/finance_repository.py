import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from app.models.finance import (
    FinancialAccount,
    FinancialCategory,
    FinancialTag,
    FinancialTransactionTag,
    FinancialTransaction,
    FinancialTransfer,
    Budget,
    RecurringFinancialTransaction,
    RecurringOccurrenceRecord,
    FinancialSavingsGoal,
    FinancialSavingsGoalEntry,
    FinancialAccountType,
    FinancialTransactionType,
    FinancialCategoryType,
    RecurringFrequency,
    SavingsGoalStatus,
)
from app.schemas.finance import (
    FinancialAccountCreate,
    FinancialAccountUpdate,
    BalanceAdjustmentCreate,
    FinancialCategoryCreate,
    FinancialCategoryUpdate,
    FinancialTagCreate,
    FinancialTransactionCreate,
    FinancialTransactionUpdate,
    FinancialTransferCreate,
    BudgetCreate,
    BudgetUpdate,
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    FinancialSavingsGoalCreate,
    FinancialSavingsGoalUpdate,
    SavingsGoalEntryCreate,
)

DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "#10B981", "briefcase"),
    ("Freelance", "#06B6D4", "laptop"),
    ("Business", "#3B82F6", "trending-up"),
    ("Investments", "#8B5CF6", "pie-chart"),
    ("Gifts", "#EC4899", "gift"),
    ("Other Income", "#6B7280", "plus-circle"),
]

DEFAULT_EXPENSE_CATEGORIES = [
    ("Food & Dining", "#EF4444", "utensils"),
    ("Groceries", "#F59E0B", "shopping-cart"),
    ("Rent & Housing", "#6366F1", "home"),
    ("Transportation", "#3B82F6", "truck"),
    ("Shopping", "#EC4899", "shopping-bag"),
    ("Entertainment", "#8B5CF6", "film"),
    ("Healthcare", "#14B8A6", "activity"),
    ("Education", "#06B6D4", "book-open"),
    ("Utilities", "#F97316", "zap"),
    ("Subscriptions", "#84CC16", "repeat"),
    ("Travel", "#0EA5E9", "globe"),
    ("Other Expense", "#6B7280", "minus-circle"),
]


class FinanceRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------ Accounts ------------------
    def get_account_by_id(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialAccount]:
        return self.db.query(FinancialAccount).filter(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id
        ).first()

    def get_accounts_by_user(self, user_id: uuid.UUID, include_archived: bool = False) -> List[FinancialAccount]:
        query = self.db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id)
        if not include_archived:
            query = query.filter(FinancialAccount.is_archived.is_(False))
        return query.order_by(FinancialAccount.name.asc()).all()

    def create_account(self, user_id: uuid.UUID, data: FinancialAccountCreate) -> FinancialAccount:
        account = FinancialAccount(
            user_id=user_id,
            name=data.name,
            account_type=data.account_type.value if hasattr(data.account_type, "value") else data.account_type,
            currency=data.currency.upper(),
            opening_balance=data.opening_balance,
            description=data.description,
            institution_name=data.institution_name,
            color=data.color,
            icon=data.icon,
            is_archived=False,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_account(self, account: FinancialAccount, data: FinancialAccountUpdate) -> FinancialAccount:
        update_data = data.model_dump(exclude_unset=True)
        if "account_type" in update_data and update_data["account_type"]:
            val = update_data["account_type"]
            update_data["account_type"] = val.value if hasattr(val, "value") else val
        for field, value in update_data.items():
            setattr(account, field, value)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account: FinancialAccount) -> None:
        self.db.delete(account)
        self.db.commit()

    def calculate_account_balance(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Decimal:
        account = self.get_account_by_id(account_id, user_id)
        if not account:
            return Decimal("0.00")

        net_balance = account.opening_balance

        txs = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.account_id == account_id,
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.is_voided.is_(False)
        ).all()

        for tx in txs:
            if tx.transaction_type == "INCOME":
                if account.account_type == "CREDIT_CARD":
                    net_balance -= tx.amount
                else:
                    net_balance += tx.amount
            elif tx.transaction_type == "EXPENSE":
                if account.account_type == "CREDIT_CARD":
                    net_balance += tx.amount
                else:
                    net_balance -= tx.amount
            elif tx.transaction_type == "ADJUSTMENT":
                net_balance += tx.amount
            elif tx.transaction_type == "TRANSFER":
                if tx.transfer:
                    if tx.transfer.source_account_id == account_id:
                        net_balance -= tx.amount
                    elif tx.transfer.destination_account_id == account_id:
                        net_balance += tx.amount
                else:
                    net_balance += tx.amount

        return net_balance

    # ------------------ Categories ------------------
    def get_categories_by_user(self, user_id: uuid.UUID) -> List[FinancialCategory]:
        return self.db.query(FinancialCategory).filter(
            FinancialCategory.user_id == user_id,
            FinancialCategory.is_archived.is_(False)
        ).order_by(FinancialCategory.category_type.asc(), FinancialCategory.name.asc()).all()

    def get_category_by_id(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialCategory]:
        return self.db.query(FinancialCategory).filter(
            FinancialCategory.id == category_id,
            FinancialCategory.user_id == user_id
        ).first()

    def create_category(self, user_id: uuid.UUID, data: FinancialCategoryCreate) -> FinancialCategory:
        cat_type = data.category_type.value if hasattr(data.category_type, "value") else data.category_type
        category = FinancialCategory(
            user_id=user_id,
            name=data.name.strip(),
            category_type=cat_type,
            color=data.color,
            icon=data.icon,
            is_default=False,
            is_archived=False,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category: FinancialCategory, data: FinancialCategoryUpdate) -> FinancialCategory:
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"]:
            update_data["name"] = update_data["name"].strip()
        for field, value in update_data.items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category: FinancialCategory) -> None:
        self.db.delete(category)
        self.db.commit()

    def seed_default_categories(self, user_id: uuid.UUID) -> List[FinancialCategory]:
        existing = self.db.query(FinancialCategory).filter(FinancialCategory.user_id == user_id).first()
        if existing:
            return self.get_categories_by_user(user_id)

        created = []
        for name, color, icon in DEFAULT_INCOME_CATEGORIES:
            cat = FinancialCategory(
                user_id=user_id,
                name=name,
                category_type="INCOME",
                color=color,
                icon=icon,
                is_default=True,
                is_archived=False,
            )
            self.db.add(cat)
            created.append(cat)

        for name, color, icon in DEFAULT_EXPENSE_CATEGORIES:
            cat = FinancialCategory(
                user_id=user_id,
                name=name,
                category_type="EXPENSE",
                color=color,
                icon=icon,
                is_default=True,
                is_archived=False,
            )
            self.db.add(cat)
            created.append(cat)

        self.db.commit()
        for cat in created:
            self.db.refresh(cat)
        return created

    # ------------------ Tags ------------------
    def get_tags_by_user(self, user_id: uuid.UUID) -> List[FinancialTag]:
        return self.db.query(FinancialTag).filter(
            FinancialTag.user_id == user_id
        ).order_by(FinancialTag.name.asc()).all()

    def get_tag_by_id(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTag]:
        return self.db.query(FinancialTag).filter(
            FinancialTag.id == tag_id,
            FinancialTag.user_id == user_id
        ).first()

    def create_tag(self, user_id: uuid.UUID, data: FinancialTagCreate) -> FinancialTag:
        tag = FinancialTag(
            user_id=user_id,
            name=data.name.strip(),
            color=data.color,
        )
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete_tag(self, tag: FinancialTag) -> None:
        self.db.delete(tag)
        self.db.commit()

    # ------------------ Transactions ------------------
    def get_transaction_by_id(self, tx_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTransaction]:
        return self.db.query(FinancialTransaction).filter(
            FinancialTransaction.id == tx_id,
            FinancialTransaction.user_id == user_id
        ).first()

    def get_transactions_filtered(
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
    ) -> Tuple[List[FinancialTransaction], int]:
        query = self.db.query(FinancialTransaction).filter(FinancialTransaction.user_id == user_id)

        if account_id:
            query = query.filter(FinancialTransaction.account_id == account_id)
        if category_id:
            query = query.filter(FinancialTransaction.category_id == category_id)
        if transaction_type:
            query = query.filter(FinancialTransaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)
        if not include_voided:
            query = query.filter(FinancialTransaction.is_voided.is_(False))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    FinancialTransaction.description.ilike(pattern),
                    FinancialTransaction.merchant_or_source.ilike(pattern),
                    FinancialTransaction.notes.ilike(pattern)
                )
            )

        total = query.count()
        query = query.order_by(
            desc(FinancialTransaction.transaction_date),
            desc(FinancialTransaction.created_at)
        )
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create_transaction(
        self,
        user_id: uuid.UUID,
        data: FinancialTransactionCreate,
        transfer_id: Optional[uuid.UUID] = None
    ) -> FinancialTransaction:
        tx_type = data.transaction_type.value if hasattr(data.transaction_type, "value") else data.transaction_type
        tx = FinancialTransaction(
            user_id=user_id,
            account_id=data.account_id,
            category_id=data.category_id,
            transfer_id=transfer_id,
            transaction_type=tx_type,
            amount=data.amount,
            currency=data.currency.upper(),
            description=data.description,
            transaction_date=data.transaction_date,
            merchant_or_source=data.merchant_or_source,
            notes=data.notes,
            is_voided=False,
        )
        self.db.add(tx)
        self.db.flush()

        if data.tag_ids:
            for tid in data.tag_ids:
                tag_link = FinancialTransactionTag(transaction_id=tx.id, tag_id=tid)
                self.db.add(tag_link)

        self.db.commit()
        self.db.refresh(tx)
        return tx

    def update_transaction(
        self,
        tx: FinancialTransaction,
        data: FinancialTransactionUpdate
    ) -> FinancialTransaction:
        update_data = data.model_dump(exclude_unset=True)
        tag_ids = update_data.pop("tag_ids", None)
        if "currency" in update_data and update_data["currency"]:
            update_data["currency"] = update_data["currency"].upper()

        for field, value in update_data.items():
            setattr(tx, field, value)

        if tag_ids is not None:
            self.db.query(FinancialTransactionTag).filter(
                FinancialTransactionTag.transaction_id == tx.id
            ).delete()
            for tid in tag_ids:
                self.db.add(FinancialTransactionTag(transaction_id=tx.id, tag_id=tid))

        self.db.commit()
        self.db.refresh(tx)
        return tx

    def void_transaction(self, tx: FinancialTransaction) -> FinancialTransaction:
        tx.is_voided = True
        tx.voided_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    # ------------------ Transfers ------------------
    def get_transfer_by_id(self, transfer_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialTransfer]:
        return self.db.query(FinancialTransfer).filter(
            FinancialTransfer.id == transfer_id,
            FinancialTransfer.user_id == user_id
        ).first()

    def get_transfers_by_user(self, user_id: uuid.UUID, limit: int = 50, skip: int = 0) -> Tuple[List[FinancialTransfer], int]:
        query = self.db.query(FinancialTransfer).filter(FinancialTransfer.user_id == user_id)
        total = query.count()
        transfers = query.order_by(desc(FinancialTransfer.transfer_date), desc(FinancialTransfer.created_at)).offset(skip).limit(limit).all()
        return transfers, total

    def create_transfer(
        self,
        user_id: uuid.UUID,
        data: FinancialTransferCreate,
        currency: str
    ) -> FinancialTransfer:
        transfer = FinancialTransfer(
            user_id=user_id,
            source_account_id=data.source_account_id,
            destination_account_id=data.destination_account_id,
            amount=data.amount,
            currency=currency.upper(),
            transfer_date=data.transfer_date,
            description=data.description or "Transfer between accounts",
            notes=data.notes,
            is_voided=False,
        )
        self.db.add(transfer)
        self.db.flush()

        # Paired transactions
        source_tx = FinancialTransaction(
            user_id=user_id,
            account_id=data.source_account_id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            amount=data.amount,
            currency=currency.upper(),
            transaction_date=data.transfer_date,
            description=f"Transfer to destination: {data.description or ''}".strip(),
            is_voided=False,
        )
        self.db.add(source_tx)

        dest_tx = FinancialTransaction(
            user_id=user_id,
            account_id=data.destination_account_id,
            transfer_id=transfer.id,
            transaction_type="TRANSFER",
            amount=data.amount,
            currency=currency.upper(),
            transaction_date=data.transfer_date,
            description=f"Transfer from source: {data.description or ''}".strip(),
            is_voided=False,
        )
        self.db.add(dest_tx)

        self.db.commit()
        self.db.refresh(transfer)
        return transfer

    def void_transfer(self, transfer: FinancialTransfer) -> FinancialTransfer:
        transfer.is_voided = True

        linked_txs = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.transfer_id == transfer.id,
            FinancialTransaction.user_id == transfer.user_id
        ).all()
        for tx in linked_txs:
            tx.is_voided = True
            tx.voided_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(transfer)
        return transfer

    # ------------------ Budgets ------------------
    def get_budget_by_id(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Budget]:
        return self.db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()

    def get_budgets_by_month(self, user_id: uuid.UUID, year: int, month: int) -> List[Budget]:
        return self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.year == year,
            Budget.month == month,
            Budget.is_archived.is_(False)
        ).all()

    def create_budget(self, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
        budget = Budget(
            user_id=user_id,
            name=data.name,
            category_id=data.category_id,
            amount=data.amount,
            currency=data.currency.upper(),
            year=data.year,
            month=data.month,
            alert_75_sent=False,
            alert_90_sent=False,
            alert_100_sent=False,
            is_archived=False,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def update_budget(self, budget: Budget, data: BudgetUpdate) -> Budget:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete_budget(self, budget: Budget) -> None:
        self.db.delete(budget)
        self.db.commit()

    def calculate_budget_spent(self, budget: Budget) -> Decimal:
        start_date = date(budget.year, budget.month, 1)
        if budget.month == 12:
            end_date = date(budget.year + 1, 1, 1)
        else:
            end_date = date(budget.year, budget.month + 1, 1)

        query = self.db.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter(
            FinancialTransaction.user_id == budget.user_id,
            FinancialTransaction.transaction_type == "EXPENSE",
            FinancialTransaction.is_voided.is_(False),
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date < end_date,
            FinancialTransaction.currency == budget.currency
        )
        if budget.category_id:
            query = query.filter(FinancialTransaction.category_id == budget.category_id)

        spent = query.scalar() or Decimal("0.00")
        return Decimal(str(spent))

    # ------------------ Recurring Transactions ------------------
    def get_recurring_by_id(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> Optional[RecurringFinancialTransaction]:
        return self.db.query(RecurringFinancialTransaction).filter(
            RecurringFinancialTransaction.id == rule_id,
            RecurringFinancialTransaction.user_id == user_id
        ).first()

    def get_recurring_rules_by_user(self, user_id: uuid.UUID) -> List[RecurringFinancialTransaction]:
        return self.db.query(RecurringFinancialTransaction).filter(
            RecurringFinancialTransaction.user_id == user_id
        ).order_by(RecurringFinancialTransaction.next_occurrence.asc()).all()

    def get_due_recurring_rules(self, as_of_date: date) -> List[RecurringFinancialTransaction]:
        return self.db.query(RecurringFinancialTransaction).filter(
            RecurringFinancialTransaction.is_active.is_(True),
            RecurringFinancialTransaction.next_occurrence <= as_of_date,
            or_(
                RecurringFinancialTransaction.end_date.is_(None),
                RecurringFinancialTransaction.end_date >= RecurringFinancialTransaction.next_occurrence
            )
        ).all()

    def create_recurring_rule(self, user_id: uuid.UUID, data: RecurringTransactionCreate) -> RecurringFinancialTransaction:
        freq = data.frequency.value if hasattr(data.frequency, "value") else data.frequency
        tx_type = data.transaction_type.value if hasattr(data.transaction_type, "value") else data.transaction_type
        rule = RecurringFinancialTransaction(
            user_id=user_id,
            account_id=data.account_id,
            category_id=data.category_id,
            transaction_type=tx_type,
            amount=data.amount,
            currency=data.currency.upper(),
            description=data.description,
            merchant_or_source=data.merchant_or_source,
            frequency=freq,
            start_date=data.start_date,
            end_date=data.end_date,
            next_occurrence=data.start_date,
            is_active=True,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_recurring_rule(self, rule: RecurringFinancialTransaction, data: RecurringTransactionUpdate) -> RecurringFinancialTransaction:
        update_data = data.model_dump(exclude_unset=True)
        if "frequency" in update_data and update_data["frequency"]:
            val = update_data["frequency"]
            update_data["frequency"] = val.value if hasattr(val, "value") else val
        for field, value in update_data.items():
            setattr(rule, field, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_recurring_rule(self, rule: RecurringFinancialTransaction) -> None:
        self.db.delete(rule)
        self.db.commit()

    def record_recurring_occurrence(self, rule_id: uuid.UUID, occurrence_date: date, tx_id: uuid.UUID) -> RecurringOccurrenceRecord:
        record = RecurringOccurrenceRecord(
            recurring_rule_id=rule_id,
            occurrence_date=occurrence_date,
            generated_transaction_id=tx_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def has_occurrence_record(self, rule_id: uuid.UUID, occurrence_date: date) -> bool:
        exists = self.db.query(RecurringOccurrenceRecord).filter(
            RecurringOccurrenceRecord.recurring_rule_id == rule_id,
            RecurringOccurrenceRecord.occurrence_date == occurrence_date
        ).first()
        return exists is not None

    # ------------------ Savings Goals ------------------
    def get_savings_goal_by_id(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> Optional[FinancialSavingsGoal]:
        return self.db.query(FinancialSavingsGoal).filter(
            FinancialSavingsGoal.id == goal_id,
            FinancialSavingsGoal.user_id == user_id
        ).first()

    def get_savings_goals_by_user(self, user_id: uuid.UUID) -> List[FinancialSavingsGoal]:
        return self.db.query(FinancialSavingsGoal).filter(
            FinancialSavingsGoal.user_id == user_id,
            FinancialSavingsGoal.status != SavingsGoalStatus.ARCHIVED.value
        ).order_by(FinancialSavingsGoal.created_at.desc()).all()

    def create_savings_goal(self, user_id: uuid.UUID, data: FinancialSavingsGoalCreate) -> FinancialSavingsGoal:
        goal = FinancialSavingsGoal(
            user_id=user_id,
            title=data.title,
            description=data.description,
            target_amount=data.target_amount,
            currency=data.currency.upper(),
            target_date=data.target_date,
            productivity_goal_id=data.productivity_goal_id,
            status=SavingsGoalStatus.ACTIVE.value,
            deadline_reminder_sent=False,
            completed_notification_sent=False,
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def update_savings_goal(self, goal: FinancialSavingsGoal, data: FinancialSavingsGoalUpdate) -> FinancialSavingsGoal:
        update_data = data.model_dump(exclude_unset=True)
        if "status" in update_data and update_data["status"]:
            val = update_data["status"]
            update_data["status"] = val.value if hasattr(val, "value") else val
        for field, value in update_data.items():
            setattr(goal, field, value)

        self.db.commit()
        self.db.refresh(goal)
        return goal

    def delete_savings_goal(self, goal: FinancialSavingsGoal) -> None:
        self.db.delete(goal)
        self.db.commit()

    def calculate_savings_goal_current(self, goal_id: uuid.UUID) -> Decimal:
        deposits = self.db.query(func.coalesce(func.sum(FinancialSavingsGoalEntry.amount), 0)).filter(
            FinancialSavingsGoalEntry.savings_goal_id == goal_id,
            FinancialSavingsGoalEntry.entry_type == "DEPOSIT"
        ).scalar() or Decimal("0.00")

        withdrawals = self.db.query(func.coalesce(func.sum(FinancialSavingsGoalEntry.amount), 0)).filter(
            FinancialSavingsGoalEntry.savings_goal_id == goal_id,
            FinancialSavingsGoalEntry.entry_type == "WITHDRAWAL"
        ).scalar() or Decimal("0.00")

        return max(Decimal("0.00"), Decimal(str(deposits)) - Decimal(str(withdrawals)))

    def add_savings_entry(self, user_id: uuid.UUID, goal_id: uuid.UUID, data: SavingsGoalEntryCreate) -> FinancialSavingsGoalEntry:
        entry = FinancialSavingsGoalEntry(
            savings_goal_id=goal_id,
            user_id=user_id,
            account_id=data.account_id,
            entry_type=data.entry_type,
            amount=data.amount,
            entry_date=data.entry_date,
            notes=data.notes,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        # Check completion
        goal = self.get_savings_goal_by_id(goal_id, user_id)
        if goal:
            curr = self.calculate_savings_goal_current(goal_id)
            if curr >= goal.target_amount and goal.status == SavingsGoalStatus.ACTIVE.value:
                goal.status = SavingsGoalStatus.COMPLETED.value
                self.db.commit()
            elif curr < goal.target_amount and goal.status == SavingsGoalStatus.COMPLETED.value:
                goal.status = SavingsGoalStatus.ACTIVE.value
                self.db.commit()

        return entry
