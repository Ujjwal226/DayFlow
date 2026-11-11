"""create goals, goal_milestones, goal_task_links, planning_objectives, and goal_activities tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-11 04:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. goals table
    op.create_table(
        'goals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=32), server_default='PERSONAL', nullable=False),
        sa.Column('goal_type', sa.String(length=32), server_default='OUTCOME', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='NOT_STARTED', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('progress_method', sa.String(length=32), server_default='MANUAL', nullable=False),
        sa.Column('progress_percentage', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_goals_project_id_projects', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_goals_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'], unique=False)
    op.create_index(op.f('ix_goals_project_id'), 'goals', ['project_id'], unique=False)
    op.create_index(op.f('ix_goals_category'), 'goals', ['category'], unique=False)
    op.create_index(op.f('ix_goals_goal_type'), 'goals', ['goal_type'], unique=False)
    op.create_index(op.f('ix_goals_status'), 'goals', ['status'], unique=False)
    op.create_index(op.f('ix_goals_priority'), 'goals', ['priority'], unique=False)
    op.create_index(op.f('ix_goals_target_date'), 'goals', ['target_date'], unique=False)
    op.create_index(op.f('ix_goals_is_archived'), 'goals', ['is_archived'], unique=False)
    op.create_index('ix_goals_user_status', 'goals', ['user_id', 'status'], unique=False)
    op.create_index('ix_goals_user_category', 'goals', ['user_id', 'category'], unique=False)
    op.create_index('ix_goals_user_target_date', 'goals', ['user_id', 'target_date'], unique=False)
    op.create_index('ix_goals_user_archived', 'goals', ['user_id', 'is_archived'], unique=False)

    # 2. goal_milestones table
    op.create_table(
        'goal_milestones',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name='fk_goal_milestones_goal_id_goals', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_goal_milestones_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_milestones_goal_id'), 'goal_milestones', ['goal_id'], unique=False)
    op.create_index(op.f('ix_goal_milestones_user_id'), 'goal_milestones', ['user_id'], unique=False)
    op.create_index(op.f('ix_goal_milestones_is_completed'), 'goal_milestones', ['is_completed'], unique=False)
    op.create_index('ix_goal_milestones_user_goal', 'goal_milestones', ['user_id', 'goal_id'], unique=False)

    # 3. goal_task_links table
    op.create_table(
        'goal_task_links',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name='fk_goal_task_links_goal_id_goals', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_goal_task_links_task_id_tasks', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('goal_id', 'task_id', name='uq_goal_task_link')
    )
    op.create_index(op.f('ix_goal_task_links_goal_id'), 'goal_task_links', ['goal_id'], unique=False)
    op.create_index(op.f('ix_goal_task_links_task_id'), 'goal_task_links', ['task_id'], unique=False)

    # 4. planning_objectives table
    op.create_table(
        'planning_objectives',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name='fk_planning_objectives_goal_id_goals', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_planning_objectives_task_id_tasks', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_planning_objectives_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_planning_objectives_user_id'), 'planning_objectives', ['user_id'], unique=False)
    op.create_index(op.f('ix_planning_objectives_goal_id'), 'planning_objectives', ['goal_id'], unique=False)
    op.create_index(op.f('ix_planning_objectives_task_id'), 'planning_objectives', ['task_id'], unique=False)
    op.create_index(op.f('ix_planning_objectives_period_type'), 'planning_objectives', ['period_type'], unique=False)
    op.create_index(op.f('ix_planning_objectives_period_date'), 'planning_objectives', ['period_date'], unique=False)
    op.create_index(op.f('ix_planning_objectives_is_completed'), 'planning_objectives', ['is_completed'], unique=False)
    op.create_index('ix_planning_objectives_user_period', 'planning_objectives', ['user_id', 'period_type', 'period_date'], unique=False)

    # 5. goal_activities table
    op.create_table(
        'goal_activities',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('old_value', sa.String(length=200), nullable=True),
        sa.Column('new_value', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name='fk_goal_activities_goal_id_goals', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_goal_activities_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_activities_goal_id'), 'goal_activities', ['goal_id'], unique=False)
    op.create_index(op.f('ix_goal_activities_user_id'), 'goal_activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_goal_activities_created_at'), 'goal_activities', ['created_at'], unique=False)
    op.create_index('ix_goal_activities_goal_created', 'goal_activities', ['goal_id', 'created_at'], unique=False)
    op.create_index('ix_goal_activities_user_created', 'goal_activities', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('goal_activities')
    op.drop_table('planning_objectives')
    op.drop_table('goal_task_links')
    op.drop_table('goal_milestones')
    op.drop_table('goals')
