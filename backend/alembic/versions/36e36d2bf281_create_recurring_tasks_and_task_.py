"""create recurring tasks and task recurrence fields

Revision ID: 36e36d2bf281
Revises: 7e8866728b79
Create Date: 2026-11-04 04:24:17.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '36e36d2bf281'
down_revision: Union[str, None] = '7e8866728b79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Conditionally create recurrence_frequency Enum in PostgreSQL
    recurrence_frequency_enum = postgresql.ENUM(
        'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM',
        name='recurrence_frequency',
        create_type=False,
    )
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recurrence_frequency') THEN
                CREATE TYPE recurrence_frequency AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM');
            END IF;
        END$$;
    """))

    task_priority_enum = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'URGENT',
        name='task_priority',
        create_type=False,
    )

    # 2. Create recurring_tasks table
    op.create_table(
        'recurring_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', task_priority_enum, nullable=False, server_default='MEDIUM'),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('frequency', recurrence_frequency_enum, nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('max_occurrences', sa.Integer(), nullable=True),
        sa.Column('weekdays', sa.String(length=50), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('month_of_year', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True, server_default='UTC'),
        sa.Column('next_occurrence_date', sa.Date(), nullable=True),
        sa.Column('occurrences_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_stopped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recurring_tasks_user_id'), 'recurring_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_category_id'), 'recurring_tasks', ['category_id'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_project_id'), 'recurring_tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_frequency'), 'recurring_tasks', ['frequency'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_next_occurrence_date'), 'recurring_tasks', ['next_occurrence_date'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_is_active'), 'recurring_tasks', ['is_active'], unique=False)
    op.create_index(op.f('ix_recurring_tasks_is_stopped'), 'recurring_tasks', ['is_stopped'], unique=False)
    op.create_index(
        'ix_recurring_tasks_user_active_next',
        'recurring_tasks',
        ['user_id', 'is_active', 'is_stopped', 'next_occurrence_date'],
        unique=False,
    )

    # 3. Create recurring_task_skips table
    op.create_table(
        'recurring_task_skips',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('recurring_task_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('skip_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recurring_task_id'], ['recurring_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recurring_task_id', 'skip_date', name='uq_recurring_task_skips_task_date'),
    )
    op.create_index(op.f('ix_recurring_task_skips_recurring_task_id'), 'recurring_task_skips', ['recurring_task_id'], unique=False)
    op.create_index(op.f('ix_recurring_task_skips_user_id'), 'recurring_task_skips', ['user_id'], unique=False)
    op.create_index('ix_recurring_task_skips_task_date', 'recurring_task_skips', ['recurring_task_id', 'skip_date'], unique=False)

    # 4. Add recurrence fields to tasks table
    op.add_column('tasks', sa.Column('recurring_task_id', sa.Uuid(), nullable=True))
    op.add_column('tasks', sa.Column('occurrence_date', sa.Date(), nullable=True))
    op.add_column('tasks', sa.Column('occurrence_index', sa.Integer(), nullable=True))

    op.create_index(op.f('ix_tasks_recurring_task_id'), 'tasks', ['recurring_task_id'], unique=False)
    op.create_index(op.f('ix_tasks_occurrence_date'), 'tasks', ['occurrence_date'], unique=False)
    op.create_index('ix_tasks_user_id_recurring_task_id', 'tasks', ['user_id', 'recurring_task_id'], unique=False)
    op.create_unique_constraint('uq_tasks_recurring_task_occurrence_date', 'tasks', ['recurring_task_id', 'occurrence_date'])

    op.create_foreign_key(
        'fk_tasks_recurring_task_id_recurring_tasks',
        'tasks',
        'recurring_tasks',
        ['recurring_task_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    # 1. Drop recurrence foreign keys, indexes, and columns from tasks table
    op.drop_constraint('fk_tasks_recurring_task_id_recurring_tasks', 'tasks', type_='foreignkey')
    op.drop_constraint('uq_tasks_recurring_task_occurrence_date', 'tasks', type_='unique')
    op.drop_index('ix_tasks_user_id_recurring_task_id', table_name='tasks')
    op.drop_index(op.f('ix_tasks_occurrence_date'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_recurring_task_id'), table_name='tasks')
    op.drop_column('tasks', 'occurrence_index')
    op.drop_column('tasks', 'occurrence_date')
    op.drop_column('tasks', 'recurring_task_id')

    # 2. Drop recurring_task_skips table
    op.drop_index('ix_recurring_task_skips_task_date', table_name='recurring_task_skips')
    op.drop_index(op.f('ix_recurring_task_skips_user_id'), table_name='recurring_task_skips')
    op.drop_index(op.f('ix_recurring_task_skips_recurring_task_id'), table_name='recurring_task_skips')
    op.drop_table('recurring_task_skips')

    # 3. Drop recurring_tasks table
    op.drop_index('ix_recurring_tasks_user_active_next', table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_is_stopped'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_is_active'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_next_occurrence_date'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_frequency'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_project_id'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_category_id'), table_name='recurring_tasks')
    op.drop_index(op.f('ix_recurring_tasks_user_id'), table_name='recurring_tasks')
    op.drop_table('recurring_tasks')

    # 4. Drop Enum
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recurrence_frequency') THEN
                DROP TYPE recurrence_frequency;
            END IF;
        END$$;
    """))
