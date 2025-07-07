"""initial

Revision ID: 2a5f4c125692
Revises: 
Create Date: 2025-06-28 13:23:45.618361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2a5f4c125692'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('questions',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('test_id', sa.Integer(), nullable=False),
    sa.Column('exam_type', sa.String(length=50), nullable=False),
    sa.Column('question_set_id', sa.String(length=255), nullable=False),
    sa.Column('question', sa.String(), nullable=False),
    sa.Column('answer_1', sa.String(), nullable=False),
    sa.Column('answer_2', sa.String(), nullable=False),
    sa.Column('answer_3', sa.String(), nullable=False),
    sa.Column('answer_4', sa.String(), nullable=False),
    sa.Column('solution', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_test_id'), 'questions', ['test_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('questions')

