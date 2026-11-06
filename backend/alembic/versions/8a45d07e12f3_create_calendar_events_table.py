"""create_calendar_events_table

Revision ID: 8a45d07e12f3
Revises: 7c32b50d9e11
Create Date: 2026-11-07 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a45d07e12f3'
down_revision: Union[str, None] = '7c32b50d9e11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            '(is_all_day = false AND start_at IS NOT NULL AND end_at IS NOT NULL AND end_at > start_at AND start_date IS NULL AND end_date IS NULL) OR '
            '(is_all_day = true AND start_date IS NOT NULL AND end_date IS NOT NULL AND end_date > start_date AND start_at IS NULL AND end_at IS NULL)',
            name='ck_calendar_events_valid_representation'
        ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_events_end_at'), 'calendar_events', ['end_at'], unique=False)
    op.create_index(op.f('ix_calendar_events_end_date'), 'calendar_events', ['end_date'], unique=False)
    op.create_index(op.f('ix_calendar_events_is_all_day'), 'calendar_events', ['is_all_day'], unique=False)
    op.create_index(op.f('ix_calendar_events_start_at'), 'calendar_events', ['start_at'], unique=False)
    op.create_index(op.f('ix_calendar_events_start_date'), 'calendar_events', ['start_date'], unique=False)
    op.create_index(op.f('ix_calendar_events_task_id'), 'calendar_events', ['task_id'], unique=False)
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)
    op.create_index('ix_calendar_events_user_start_at', 'calendar_events', ['user_id', 'start_at'], unique=False)
    op.create_index('ix_calendar_events_user_start_date', 'calendar_events', ['user_id', 'start_date'], unique=False)
    op.create_index('ix_calendar_events_user_task_id', 'calendar_events', ['user_id', 'task_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_calendar_events_user_task_id', table_name='calendar_events')
    op.drop_index('ix_calendar_events_user_start_date', table_name='calendar_events')
    op.drop_index('ix_calendar_events_user_start_at', table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_task_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_start_date'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_start_at'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_is_all_day'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_end_date'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_end_at'), table_name='calendar_events')
    op.drop_table('calendar_events')

