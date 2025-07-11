"""added logging db

Revision ID: 71714ff79e20
Revises: 2a5f4c125692
Create Date: 2025-06-30 19:39:10.471008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision: str = '71714ff79e20'
down_revision: Union[str, Sequence[str], None] = '2a5f4c125692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'answer_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id'), nullable=False, index=True),
        sa.Column('selected_answer', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False), 
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Add opinion_logs table
    op.create_table(
        'opinion_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id'), nullable=False, index=True),
        sa.Column('up', sa.Boolean(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False), 
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'question_sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_set_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id'), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
    )

def downgrade():
    op.drop_table('question_sets')
    op.drop_table('opinion_logs')
    op.drop_table('answer_logs')


