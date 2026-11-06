"""create_dashboard_layouts_table

Revision ID: 7c32b50d9e11
Revises: 62163e1a7a8c
Create Date: 2026-11-07 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7c32b50d9e11'
down_revision: Union[str, None] = '62163e1a7a8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use JSONB on PostgreSQL, otherwise standard JSON
    json_type = postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == "postgresql" else sa.JSON()

    op.create_table(
        'dashboard_layouts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('widgets', json_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_dashboard_layouts_user_id'), 'dashboard_layouts', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_dashboard_layouts_user_id'), table_name='dashboard_layouts')
    op.drop_table('dashboard_layouts')

