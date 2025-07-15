"""add_specifications_table

Revision ID: c5e806a80bcc
Revises: 71714ff79e20
Create Date: 2025-07-15 21:36:07.729060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e806a80bcc'
down_revision: Union[str, Sequence[str], None] = '71714ff79e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'specifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exam', sa.String(length=50), nullable=False, index=True),
        sa.Column('topic', sa.String(length=255), nullable=False, index=True),
        sa.Column('specification', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('specifications')
