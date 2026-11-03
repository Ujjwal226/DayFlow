"""create projects and add project_id to tasks

Revision ID: 7e8866728b79
Revises: 84790214dd00
Create Date: 2026-11-04 03:22:17.773263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7e8866728b79'
down_revision: Union[str, None] = '84790214dd00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Define PostgreSQL ENUMs with create_type=False so create_table uses them safely
    project_status_enum = postgresql.ENUM(
        'PLANNED', 'ACTIVE', 'ON_HOLD', 'COMPLETED',
        name='project_status',
        create_type=False
    )
    project_priority_enum = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'URGENT',
        name='project_priority',
        create_type=False
    )

    # Conditionally create the types in PostgreSQL if they don't already exist
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
                CREATE TYPE project_status AS ENUM ('PLANNED', 'ACTIVE', 'ON_HOLD', 'COMPLETED');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_priority') THEN
                CREATE TYPE project_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');
            END IF;
        END$$;
    """))

    # 2. Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status',
            project_status_enum,
            nullable=False,
            server_default='PLANNED',
        ),
        sa.Column(
            'priority',
            project_priority_enum,
            nullable=False,
            server_default='MEDIUM',
        ),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True, server_default='#3B82F6'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_priority'), 'projects', ['priority'], unique=False)
    op.create_index(op.f('ix_projects_due_date'), 'projects', ['due_date'], unique=False)
    op.create_index(op.f('ix_projects_is_archived'), 'projects', ['is_archived'], unique=False)

    op.create_index('ix_projects_user_id_status', 'projects', ['user_id', 'status'], unique=False)
    op.create_index('ix_projects_user_id_priority', 'projects', ['user_id', 'priority'], unique=False)
    op.create_index('ix_projects_user_id_is_archived', 'projects', ['user_id', 'is_archived'], unique=False)
    op.create_index('ix_projects_user_id_due_date', 'projects', ['user_id', 'due_date'], unique=False)
    op.create_index('ix_projects_user_id_created_at', 'projects', ['user_id', 'created_at'], unique=False)

    # 3. Add nullable project_id column to tasks table with SET NULL on project deletion
    op.add_column('tasks', sa.Column('project_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    op.create_index('ix_tasks_user_id_project_id', 'tasks', ['user_id', 'project_id'], unique=False)

    op.create_foreign_key(
        'fk_tasks_project_id_projects',
        'tasks',
        'projects',
        ['project_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # 1. Drop foreign key and columns from tasks table
    op.drop_constraint('fk_tasks_project_id_projects', 'tasks', type_='foreignkey')
    op.drop_index('ix_tasks_user_id_project_id', table_name='tasks')
    op.drop_index(op.f('ix_tasks_project_id'), table_name='tasks')
    op.drop_column('tasks', 'project_id')

    # 2. Drop projects table and indexes
    op.drop_index('ix_projects_user_id_created_at', table_name='projects')
    op.drop_index('ix_projects_user_id_due_date', table_name='projects')
    op.drop_index('ix_projects_user_id_is_archived', table_name='projects')
    op.drop_index('ix_projects_user_id_priority', table_name='projects')
    op.drop_index('ix_projects_user_id_status', table_name='projects')
    op.drop_index(op.f('ix_projects_is_archived'), table_name='projects')
    op.drop_index(op.f('ix_projects_due_date'), table_name='projects')
    op.drop_index(op.f('ix_projects_priority'), table_name='projects')
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_table('projects')

    # 3. Drop enums
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_priority') THEN
                DROP TYPE project_priority;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
                DROP TYPE project_status;
            END IF;
        END$$;
    """))
