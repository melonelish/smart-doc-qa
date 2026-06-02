"""add sequence column to conversation_records

Revision ID: a1b2c3d4e5f6
Revises: f18e19b1bcab
Create Date: 2026-06-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f18e19b1bcab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'conversation_records',
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0', comment='Sequence number within conversation'),
    )


def downgrade() -> None:
    op.drop_column('conversation_records', 'sequence')