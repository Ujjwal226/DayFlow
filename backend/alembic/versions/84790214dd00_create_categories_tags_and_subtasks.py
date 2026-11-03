"""create categories tags and subtasks

Revision ID: 84790214dd00
Revises: da9c4c1420fc
Create Date: 2026-11-04 02:28:36.276694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84790214dd00'
down_revision: Union[str, None] = 'da9c4c1420fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_normalized', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name_normalized', name='uq_categories_user_id_name_normalized')
    )
    op.create_index(op.f('ix_categories_user_id'), 'categories', ['user_id'], unique=False)
    op.create_index('ix_categories_user_id_name_normalized', 'categories', ['user_id', 'name_normalized'], unique=False)

    # 2. Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('name_normalized', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name_normalized', name='uq_tags_user_id_name_normalized')
    )
    op.create_index(op.f('ix_tags_user_id'), 'tags', ['user_id'], unique=False)
    op.create_index('ix_tags_user_id_name_normalized', 'tags', ['user_id', 'name_normalized'], unique=False)

    # 3. Create task_tags association table
    op.create_table(
        'task_tags',
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id'),
        sa.UniqueConstraint('task_id', 'tag_id', name='uq_task_tags_task_id_tag_id')
    )
    op.create_index(op.f('ix_task_tags_tag_id'), 'task_tags', ['tag_id'], unique=False)
    op.create_index('ix_task_tags_tag_id_task_id', 'task_tags', ['tag_id', 'task_id'], unique=False)

    # 4. Add nullable category_id and parent_task_id columns to tasks
    op.add_column('tasks', sa.Column('category_id', sa.Uuid(), nullable=True))
    op.add_column('tasks', sa.Column('parent_task_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_tasks_category_id'), 'tasks', ['category_id'], unique=False)
    op.create_index(op.f('ix_tasks_parent_task_id'), 'tasks', ['parent_task_id'], unique=False)
    op.create_index('ix_tasks_user_id_category_id', 'tasks', ['user_id', 'category_id'], unique=False)
    op.create_index('ix_tasks_user_id_parent_task_id', 'tasks', ['user_id', 'parent_task_id'], unique=False)

    # Explicit foreign key constraint names for robust downgrade
    op.create_foreign_key('fk_tasks_category_id_categories', 'tasks', 'categories', ['category_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_tasks_parent_task_id_tasks', 'tasks', 'tasks', ['parent_task_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 1. Drop foreign keys on tasks
    op.drop_constraint('fk_tasks_parent_task_id_tasks', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_category_id_categories', 'tasks', type_='foreignkey')

    # 2. Drop task indexes and columns
    op.drop_index('ix_tasks_user_id_parent_task_id', table_name='tasks')
    op.drop_index('ix_tasks_user_id_category_id', table_name='tasks')
    op.drop_index(op.f('ix_tasks_parent_task_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_category_id'), table_name='tasks')
    op.drop_column('tasks', 'parent_task_id')
    op.drop_column('tasks', 'category_id')

    # 3. Drop task_tags table
    op.drop_index('ix_task_tags_tag_id_task_id', table_name='task_tags')
    op.drop_index(op.f('ix_task_tags_tag_id'), table_name='task_tags')
    op.drop_table('task_tags')

    # 4. Drop tags table
    op.drop_index('ix_tags_user_id_name_normalized', table_name='tags')
    op.drop_index(op.f('ix_tags_user_id'), table_name='tags')
    op.drop_table('tags')

    # 5. Drop categories table
    op.drop_index('ix_categories_user_id_name_normalized', table_name='categories')
    op.drop_index(op.f('ix_categories_user_id'), table_name='categories')
    op.drop_table('categories')
