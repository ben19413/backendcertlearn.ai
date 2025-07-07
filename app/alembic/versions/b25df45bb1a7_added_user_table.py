"""added user table

Revision ID: b25df45bb1a7
Revises: 71714ff79e20
Create Date: 2025-07-07 19:08:52.689741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision: str = 'b25df45bb1a7'
down_revision: Union[str, Sequence[str], None] = '71714ff79e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema: create users table with unique username/provider and index on id."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('provider', sa.String(length=255), nullable=True),
        sa.Column('fullname', sa.String(length=255), nullable=True),
        sa.Column('register_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', 'provider', name='unique_username_per_provider')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop users table and its index/constraint."""
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
