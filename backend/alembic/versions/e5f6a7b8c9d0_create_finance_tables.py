"""create personal finance tables (accounts, categories, tags, transactions, transfers, budgets, recurring rules, and savings goals)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-12 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. financial_accounts
    op.create_table(
        'financial_accounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('account_type', sa.String(length=32), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('opening_balance', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('institution_name', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_accounts_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_accounts_user_id'), 'financial_accounts', ['user_id'], unique=False)
    op.create_index('ix_financial_accounts_user_type', 'financial_accounts', ['user_id', 'account_type'], unique=False)
    op.create_index('ix_financial_accounts_user_archived', 'financial_accounts', ['user_id', 'is_archived'], unique=False)

    # 2. financial_categories
    op.create_table(
        'financial_categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category_type', sa.String(length=20), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_categories_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'category_type', name='uq_user_category_name_type')
    )
    op.create_index(op.f('ix_financial_categories_user_id'), 'financial_categories', ['user_id'], unique=False)
    op.create_index('ix_financial_categories_user_type', 'financial_categories', ['user_id', 'category_type'], unique=False)

    # 3. financial_tags
    op.create_table(
        'financial_tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_tags_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_financial_tag_name')
    )
    op.create_index(op.f('ix_financial_tags_user_id'), 'financial_tags', ['user_id'], unique=False)

    # 4. financial_transfers
    op.create_table(
        'financial_transfers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('source_account_id', sa.Uuid(), nullable=False),
        sa.Column('destination_account_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('transfer_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_voided', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_transfers_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_account_id'], ['financial_accounts.id'], name='fk_fin_transfers_src_account', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['destination_account_id'], ['financial_accounts.id'], name='fk_fin_transfers_dst_account', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_transfers_user_id'), 'financial_transfers', ['user_id'], unique=False)
    op.create_index(op.f('ix_financial_transfers_transfer_date'), 'financial_transfers', ['transfer_date'], unique=False)

    # 5. recurring_financial_transactions
    op.create_table(
        'recurring_financial_transactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('merchant_or_source', sa.String(length=100), nullable=True),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_occurrence', sa.Date(), nullable=False),
        sa.Column('last_generated_occurrence', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_rec_tx_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['financial_accounts.id'], name='fk_rec_tx_account_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], name='fk_rec_tx_category_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurring_financial_transactions_user_id'), 'recurring_financial_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_recurring_financial_transactions_next_occurrence'), 'recurring_financial_transactions', ['next_occurrence'], unique=False)
    op.create_index('ix_recurring_tx_active_next', 'recurring_financial_transactions', ['is_active', 'next_occurrence'], unique=False)

    # 6. financial_transactions
    op.create_table(
        'financial_transactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('transfer_id', sa.Uuid(), nullable=True),
        sa.Column('recurring_rule_id', sa.Uuid(), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('merchant_or_source', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_voided', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_tx_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['financial_accounts.id'], name='fk_fin_tx_account_id', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], name='fk_fin_tx_category_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transfer_id'], ['financial_transfers.id'], name='fk_fin_tx_transfer_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recurring_rule_id'], ['recurring_financial_transactions.id'], name='fk_fin_tx_recurring_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_transactions_user_id'), 'financial_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_financial_transactions_account_id'), 'financial_transactions', ['account_id'], unique=False)
    op.create_index(op.f('ix_financial_transactions_transaction_type'), 'financial_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_financial_transactions_transaction_date'), 'financial_transactions', ['transaction_date'], unique=False)
    op.create_index('ix_financial_tx_user_date', 'financial_transactions', ['user_id', 'transaction_date'], unique=False)
    op.create_index('ix_financial_tx_account_date', 'financial_transactions', ['account_id', 'transaction_date'], unique=False)
    op.create_index('ix_financial_tx_category_date', 'financial_transactions', ['category_id', 'transaction_date'], unique=False)

    # 7. financial_transaction_tags
    op.create_table(
        'financial_transaction_tags',
        sa.Column('transaction_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['financial_transactions.id'], name='fk_fin_tx_tags_tx_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['financial_tags.id'], name='fk_fin_tx_tags_tag_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('transaction_id', 'tag_id')
    )

    # 8. recurring_financial_occurrence_records
    op.create_table(
        'recurring_financial_occurrence_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('recurring_rule_id', sa.Uuid(), nullable=False),
        sa.Column('occurrence_date', sa.Date(), nullable=False),
        sa.Column('generated_transaction_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recurring_rule_id'], ['recurring_financial_transactions.id'], name='fk_occ_rule_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_transaction_id'], ['financial_transactions.id'], name='fk_occ_tx_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recurring_rule_id', 'occurrence_date', name='uq_recurring_rule_date')
    )

    # 9. financial_budgets
    op.create_table(
        'financial_budgets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('alert_75_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('alert_90_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('alert_100_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_budgets_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], name='fk_fin_budgets_category_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_budgets_user_id'), 'financial_budgets', ['user_id'], unique=False)
    op.create_index('ix_financial_budgets_user_period', 'financial_budgets', ['user_id', 'year', 'month'], unique=False)

    # 10. financial_savings_goals
    op.create_table(
        'financial_savings_goals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('productivity_goal_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('deadline_reminder_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('completed_notification_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_fin_savings_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['productivity_goal_id'], ['goals.id'], name='fk_fin_savings_prod_goal_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_savings_goals_user_id'), 'financial_savings_goals', ['user_id'], unique=False)
    op.create_index(op.f('ix_financial_savings_goals_status'), 'financial_savings_goals', ['status'], unique=False)

    # 11. financial_savings_goal_entries
    op.create_table(
        'financial_savings_goal_entries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('savings_goal_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_id', sa.Uuid(), nullable=True),
        sa.Column('entry_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['savings_goal_id'], ['financial_savings_goals.id'], name='fk_savings_entries_goal_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_savings_entries_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['financial_accounts.id'], name='fk_savings_entries_account_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_savings_goal_entries_savings_goal_id'), 'financial_savings_goal_entries', ['savings_goal_id'], unique=False)
    op.create_index(op.f('ix_financial_savings_goal_entries_user_id'), 'financial_savings_goal_entries', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('financial_savings_goal_entries')
    op.drop_table('financial_savings_goals')
    op.drop_table('financial_budgets')
    op.drop_table('recurring_financial_occurrence_records')
    op.drop_table('financial_transaction_tags')
    op.drop_table('financial_transactions')
    op.drop_table('recurring_financial_transactions')
    op.drop_table('financial_transfers')
    op.drop_table('financial_tags')
    op.drop_table('financial_categories')
    op.drop_table('financial_accounts')
