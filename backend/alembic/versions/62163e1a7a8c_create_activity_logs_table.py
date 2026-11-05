"""create_activity_logs_table

Revision ID: 62163e1a7a8c
Revises: 36e36d2bf281
Create Date: 2026-11-06 01:32:42.681047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '62163e1a7a8c'
down_revision: Union[str, None] = '36e36d2bf281'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use JSONB on PostgreSQL, otherwise standard JSON
    json_type = postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == "postgresql" else sa.JSON()

    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('recurring_task_id', sa.Uuid(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('changes', json_type, nullable=True),
        sa.Column('metadata', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recurring_task_id'], ['recurring_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_activity_logs_action'), 'activity_logs', ['action'], unique=False)
    op.create_index(op.f('ix_activity_logs_actor_id'), 'activity_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_activity_logs_created_at'), 'activity_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_logs_entity_id'), 'activity_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_activity_logs_entity_type'), 'activity_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_activity_logs_recurring_task_id'), 'activity_logs', ['recurring_task_id'], unique=False)
    op.create_index(op.f('ix_activity_logs_task_id'), 'activity_logs', ['task_id'], unique=False)
    op.create_index(op.f('ix_activity_logs_user_id'), 'activity_logs', ['user_id'], unique=False)

    # Compound queries indexes
    op.create_index('ix_activity_logs_user_created', 'activity_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_activity_logs_task_created', 'activity_logs', ['task_id', 'created_at'], unique=False)
    op.create_index('ix_activity_logs_recurring_created', 'activity_logs', ['recurring_task_id', 'created_at'], unique=False)
    op.create_index('ix_activity_logs_user_action', 'activity_logs', ['user_id', 'action'], unique=False)
    op.create_index('ix_activity_logs_user_entity', 'activity_logs', ['user_id', 'entity_type', 'entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_activity_logs_user_entity', table_name='activity_logs')
    op.drop_index('ix_activity_logs_user_action', table_name='activity_logs')
    op.drop_index('ix_activity_logs_recurring_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_task_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_user_created', table_name='activity_logs')

    op.drop_index(op.f('ix_activity_logs_user_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_task_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_recurring_task_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_entity_type'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_entity_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_created_at'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_actor_id'), table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_action'), table_name='activity_logs')

    op.drop_table('activity_logs')
