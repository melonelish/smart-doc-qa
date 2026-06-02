"""add domain column to knowledge_bases

Revision ID: c7d8e9f0a1b2
Revises: 61f7ee5bed9c
Create Date: 2026-06-02 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = '61f7ee5bed9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_bases',
        sa.Column('domain', sa.String(length=50), nullable=True,
                  comment='Domain category: enterprise / research / legal')
    )
    op.execute("UPDATE knowledge_bases SET `domain` = 'enterprise' WHERE `domain` IS NULL")


def downgrade() -> None:
    op.drop_column('knowledge_bases', 'domain')