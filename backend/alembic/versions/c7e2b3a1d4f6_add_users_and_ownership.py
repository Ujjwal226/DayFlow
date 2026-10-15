"""add_users_and_ownership

Revision ID: c7e2b3a1d4f6
Revises: ac37764daffe
Create Date: 2026-10-15 18:50:00.000000

"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import bcrypt


# revision identifiers, used by Alembic.
revision: str = 'c7e2b3a1d4f6'
down_revision: Union[str, None] = 'ac37764daffe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    # 2. Check if existing tasks exist. If so, seed a default owner user and link them.
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM tasks")).scalar()
    default_user_id = 1
    if result and result > 0:
        # Email and password for the legacy owner account MUST be set as env vars.
        # No hardcoded fallback is provided; the migration will raise if they are absent.
        default_email = os.environ["DEFAULT_USER_EMAIL"].strip().lower()
        default_password = os.environ["DEFAULT_USER_PASSWORD"]
        hashed = bcrypt.hashpw(default_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        now_utc = datetime.now(timezone.utc)

        existing_user_id = connection.execute(
            sa.text("SELECT id FROM users WHERE email = :email"),
            {"email": default_email}
        ).scalar()

        if existing_user_id:
            default_user_id = existing_user_id
        else:
            connection.execute(
                sa.text(
                    "INSERT INTO users (email, hashed_password, full_name, created_at, updated_at) "
                    "VALUES (:email, :hashed_password, :full_name, :created_at, :updated_at)"
                ),
                {
                    "email": default_email,
                    "hashed_password": hashed,
                    "full_name": "DayFlow Owner",
                    "created_at": now_utc,
                    "updated_at": now_utc,
                }
            )
            default_user_id = connection.execute(
                sa.text("SELECT id FROM users WHERE email = :email"),
                {"email": default_email}
            ).scalar()

    # 3. Add user_id column to tasks table and associate existing tasks
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))

    if result and result > 0:
        connection.execute(
            sa.text("UPDATE tasks SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": default_user_id}
        )

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key('fk_tasks_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.create_index(batch_op.f('ix_tasks_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_user_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_tasks_user_id'))
        batch_op.drop_column('user_id')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.drop_index(batch_op.f('ix_users_id'))

    op.drop_table('users')
