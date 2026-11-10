"""create notes and note_tags tables

Revision ID: 9f12a3b4c5d6
Revises: 8a45d07e12f3
Create Date: 2026-11-11 02:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f12a3b4c5d6'
down_revision: Union[str, None] = '8a45d07e12f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create notes table
    op.create_table(
        'notes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), server_default='', nullable=False),
        sa.Column('is_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='fk_notes_category_id_categories', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_notes_project_id_projects', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_notes_task_id_tasks', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notes_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notes_category_id'), 'notes', ['category_id'], unique=False)
    op.create_index(op.f('ix_notes_created_at'), 'notes', ['created_at'], unique=False)
    op.create_index(op.f('ix_notes_is_archived'), 'notes', ['is_archived'], unique=False)
    op.create_index(op.f('ix_notes_is_pinned'), 'notes', ['is_pinned'], unique=False)
    op.create_index(op.f('ix_notes_project_id'), 'notes', ['project_id'], unique=False)
    op.create_index(op.f('ix_notes_task_id'), 'notes', ['task_id'], unique=False)
    op.create_index(op.f('ix_notes_updated_at'), 'notes', ['updated_at'], unique=False)
    op.create_index(op.f('ix_notes_user_id'), 'notes', ['user_id'], unique=False)
    op.create_index('ix_notes_user_id_is_archived', 'notes', ['user_id', 'is_archived'], unique=False)
    op.create_index('ix_notes_user_id_is_pinned', 'notes', ['user_id', 'is_pinned'], unique=False)
    op.create_index('ix_notes_user_id_project_id', 'notes', ['user_id', 'project_id'], unique=False)
    op.create_index('ix_notes_user_id_task_id', 'notes', ['user_id', 'task_id'], unique=False)
    op.create_index('ix_notes_user_id_updated_at', 'notes', ['user_id', 'updated_at'], unique=False)

    # 2. Create note_tags association table
    op.create_table(
        'note_tags',
        sa.Column('note_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], name='fk_note_tags_note_id_notes', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name='fk_note_tags_tag_id_tags', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('note_id', 'tag_id')
    )
    op.create_index(op.f('ix_note_tags_tag_id'), 'note_tags', ['tag_id'], unique=False)
    op.create_index('ix_note_tags_tag_id_note_id', 'note_tags', ['tag_id', 'note_id'], unique=False)


def downgrade() -> None:
    # 1. Drop note_tags
    op.drop_index('ix_note_tags_tag_id_note_id', table_name='note_tags')
    op.drop_index(op.f('ix_note_tags_tag_id'), table_name='note_tags')
    op.drop_table('note_tags')

    # 2. Drop notes
    op.drop_index('ix_notes_user_id_updated_at', table_name='notes')
    op.drop_index('ix_notes_user_id_task_id', table_name='notes')
    op.drop_index('ix_notes_user_id_project_id', table_name='notes')
    op.drop_index('ix_notes_user_id_is_pinned', table_name='notes')
    op.drop_index('ix_notes_user_id_is_archived', table_name='notes')
    op.drop_index(op.f('ix_notes_user_id'), table_name='notes')
    op.drop_index(op.f('ix_notes_updated_at'), table_name='notes')
    op.drop_index(op.f('ix_notes_task_id'), table_name='notes')
    op.drop_index(op.f('ix_notes_project_id'), table_name='notes')
    op.drop_index(op.f('ix_notes_is_pinned'), table_name='notes')
    op.drop_index(op.f('ix_notes_is_archived'), table_name='notes')
    op.drop_index(op.f('ix_notes_created_at'), table_name='notes')
    op.drop_index(op.f('ix_notes_category_id'), table_name='notes')
    op.drop_table('notes')

