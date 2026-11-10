"""create reminders, notifications, email_deliveries, and notification_preferences tables

Revision ID: b2c3d4e5f6a7
Revises: 9f12a3b4c5d6
Create Date: 2026-11-11 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '9f12a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. reminders table
    op.create_table(
        'reminders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('recurrence', sa.String(length=32), server_default='NONE', nullable=False),
        sa.Column('delivery_channels', sa.String(length=64), server_default='IN_APP', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_reminders_task_id_tasks', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_reminders_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reminders_user_id'), 'reminders', ['user_id'], unique=False)
    op.create_index(op.f('ix_reminders_task_id'), 'reminders', ['task_id'], unique=False)
    op.create_index(op.f('ix_reminders_scheduled_at'), 'reminders', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_reminders_status'), 'reminders', ['status'], unique=False)
    op.create_index('ix_reminders_user_scheduled', 'reminders', ['user_id', 'scheduled_at'], unique=False)
    op.create_index('ix_reminders_user_status', 'reminders', ['user_id', 'status'], unique=False)
    op.create_index('ix_reminders_due_processing', 'reminders', ['status', 'scheduled_at'], unique=False)

    # 2. notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('reminder_id', sa.Uuid(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=32), server_default='REMINDER', nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], name='fk_notifications_reminder_id_reminders', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_notifications_task_id_tasks', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notifications_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_reminder_id'), 'notifications', ['reminder_id'], unique=False)
    op.create_index(op.f('ix_notifications_task_id'), 'notifications', ['task_id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'], unique=False)

    # 3. email_deliveries table
    op.create_table(
        'email_deliveries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('notification_id', sa.Uuid(), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], name='fk_email_deliveries_notification_id_notifications', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_email_deliveries_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_deliveries_user_id'), 'email_deliveries', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_deliveries_notification_id'), 'email_deliveries', ['notification_id'], unique=False)
    op.create_index(op.f('ix_email_deliveries_status'), 'email_deliveries', ['status'], unique=False)
    op.create_index(op.f('ix_email_deliveries_next_retry_at'), 'email_deliveries', ['next_retry_at'], unique=False)
    op.create_index('ix_email_deliveries_pending', 'email_deliveries', ['status', 'next_retry_at'], unique=False)

    # 4. notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('task_reminders_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('due_date_reminders_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('overdue_reminders_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('preferred_timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('quiet_hours_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notification_preferences_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_notification_preferences_user_id')
    )
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('email_deliveries')
    op.drop_table('notifications')
    op.drop_table('reminders')

