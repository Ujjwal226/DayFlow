"""create focus_sessions and focus_preferences tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-11 03:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. focus_sessions table
    op.create_table(
        'focus_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('session_type', sa.String(length=32), server_default='FOCUS', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('planned_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('actual_duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('accumulated_pause_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_focus_sessions_project_id_projects', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_focus_sessions_task_id_tasks', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_focus_sessions_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_focus_sessions_user_id'), 'focus_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_focus_sessions_task_id'), 'focus_sessions', ['task_id'], unique=False)
    op.create_index(op.f('ix_focus_sessions_project_id'), 'focus_sessions', ['project_id'], unique=False)
    op.create_index(op.f('ix_focus_sessions_status'), 'focus_sessions', ['status'], unique=False)
    op.create_index('ix_focus_sessions_user_status', 'focus_sessions', ['user_id', 'status'], unique=False)
    op.create_index('ix_focus_sessions_user_started', 'focus_sessions', ['user_id', 'started_at'], unique=False)
    op.create_index(
        'uq_focus_sessions_user_active_or_paused',
        'focus_sessions',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('ACTIVE', 'PAUSED')"),
        sqlite_where=sa.text("status IN ('ACTIVE', 'PAUSED')"),
    )

    # 2. focus_preferences table
    op.create_table(
        'focus_preferences',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('focus_duration_minutes', sa.Integer(), server_default='25', nullable=False),
        sa.Column('short_break_duration_minutes', sa.Integer(), server_default='5', nullable=False),
        sa.Column('long_break_duration_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('long_break_interval', sa.Integer(), server_default='4', nullable=False),
        sa.Column('auto_start_breaks', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('auto_start_focus', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('sound_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('browser_notifications_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('daily_goal_minutes', sa.Integer(), server_default='120', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_focus_preferences_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_focus_preferences_user_id')
    )
    op.create_index(op.f('ix_focus_preferences_user_id'), 'focus_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_table('focus_preferences')
    op.drop_index('uq_focus_sessions_user_active_or_paused', table_name='focus_sessions')
    op.drop_table('focus_sessions')
