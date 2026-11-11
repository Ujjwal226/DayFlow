import uuid
import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FinancialAccountType(str, enum.Enum):
    CASH = "CASH"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    SAVINGS_ACCOUNT = "SAVINGS_ACCOUNT"
    CREDIT_CARD = "CREDIT_CARD"
    DIGITAL_WALLET = "DIGITAL_WALLET"
    CUSTOM = "CUSTOM"


class FinancialTransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class FinancialCategoryType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class RecurringFrequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SavingsGoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


# --- Models ---

class FinancialAccount(Base):
    """Financial account owned by a user (Cash, Bank, Savings, Credit Card, Wallet, Custom)."""

    __tablename__ = "financial_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(32), default=FinancialAccountType.BANK_ACCOUNT.value, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), default=Decimal("0.00"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", backref="financial_accounts")
    transactions = relationship(
        "FinancialTransaction",
        back_populates="account",
        foreign_keys="FinancialTransaction.account_id",
        cascade="all, delete-orphan",
    )
    outgoing_transfers = relationship(
        "FinancialTransfer",
        foreign_keys="FinancialTransfer.source_account_id",
        back_populates="source_account",
    )
    incoming_transfers = relationship(
        "FinancialTransfer",
        foreign_keys="FinancialTransfer.destination_account_id",
        back_populates="destination_account",
    )

    __table_args__ = (
        Index("ix_financial_accounts_user_type", "user_id", "account_type"),
        Index("ix_financial_accounts_user_archived", "user_id", "is_archived"),
    )


class FinancialCategory(Base):
    """Categorization for income and expense transactions."""

    __tablename__ = "financial_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[str] = mapped_column(
        String(20), default=FinancialCategoryType.EXPENSE.value, nullable=False
    )
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", backref="financial_categories")
    transactions = relationship("FinancialTransaction", back_populates="category")

    __table_args__ = (
        UniqueConstraint("user_id", "name", "category_type", name="uq_user_category_name_type"),
        Index("ix_financial_categories_user_type", "user_id", "category_type"),
    )


class FinancialTag(Base):
    """Custom tags for organizing financial transactions."""

    __tablename__ = "financial_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="financial_tags")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_financial_tag_name"),
    )


class FinancialTransactionTag(Base):
    """Many-to-many relationship linking financial transactions and tags."""

    __tablename__ = "financial_transaction_tags"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_transactions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag = relationship("FinancialTag")


class FinancialTransfer(Base):
    """First-class transfer record linking two accounts owned by the same user."""

    __tablename__ = "financial_transfers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    destination_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")
    source_account = relationship(
        "FinancialAccount",
        foreign_keys=[source_account_id],
        back_populates="outgoing_transfers",
    )
    destination_account = relationship(
        "FinancialAccount",
        foreign_keys=[destination_account_id],
        back_populates="incoming_transfers",
    )


class FinancialTransaction(Base):
    """Authoritative ledger entry for income, expense, transfer side, or adjustment."""

    __tablename__ = "financial_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transfer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_transfers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    recurring_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recurring_financial_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    merchant_or_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")
    account = relationship("FinancialAccount", back_populates="transactions", foreign_keys=[account_id])
    category = relationship("FinancialCategory", back_populates="transactions")
    transfer = relationship("FinancialTransfer")
    recurring_rule = relationship("RecurringFinancialTransaction", back_populates="generated_transactions")
    tag_links = relationship(
        "FinancialTransactionTag", cascade="all, delete-orphan", lazy="joined"
    )

    __table_args__ = (
        Index("ix_financial_tx_user_date", "user_id", "transaction_date"),
        Index("ix_financial_tx_account_date", "account_id", "transaction_date"),
        Index("ix_financial_tx_category_date", "category_id", "transaction_date"),
    )


class Budget(Base):
    """Monthly budget for an overall spending ceiling or category-specific envelope."""

    __tablename__ = "financial_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)  # 1 to 12
    alert_75_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_90_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_100_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")
    category = relationship("FinancialCategory")

    __table_args__ = (
        Index("ix_financial_budgets_user_period", "user_id", "year", "month"),
    )


class RecurringFinancialTransaction(Base):
    """Recurring transaction rule automatically processed by the background scheduler."""

    __tablename__ = "recurring_financial_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant_or_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str] = mapped_column(
        String(20), default=RecurringFrequency.MONTHLY.value, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_occurrence: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    last_generated_occurrence: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")
    account = relationship("FinancialAccount")
    category = relationship("FinancialCategory")
    generated_transactions = relationship(
        "FinancialTransaction", back_populates="recurring_rule"
    )

    __table_args__ = (
        Index("ix_recurring_tx_active_next", "is_active", "next_occurrence"),
    )


class RecurringOccurrenceRecord(Base):
    """Idempotency log ensuring recurring transactions are never generated twice for the same date."""

    __tablename__ = "recurring_financial_occurrence_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recurring_rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recurring_financial_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    occurrence_date: Mapped[date] = mapped_column(Date, nullable=False)
    generated_transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("recurring_rule_id", "occurrence_date", name="uq_recurring_rule_date"),
    )


class FinancialSavingsGoal(Base):
    """Dedicated financial savings target with explicit contribution and withdrawal history."""

    __tablename__ = "financial_savings_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    productivity_goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=SavingsGoalStatus.ACTIVE.value, nullable=False, index=True
    )
    deadline_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")
    productivity_goal = relationship("Goal")
    entries = relationship(
        "FinancialSavingsGoalEntry",
        back_populates="savings_goal",
        cascade="all, delete-orphan",
    )


class FinancialSavingsGoalEntry(Base):
    """Auditable ledger entry of a deposit contribution or withdrawal against a savings goal."""

    __tablename__ = "financial_savings_goal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    savings_goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_savings_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("financial_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    # DEPOSIT or WITHDRAWAL
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    savings_goal = relationship("FinancialSavingsGoal", back_populates="entries")
    user = relationship("User")
    account = relationship("FinancialAccount")
