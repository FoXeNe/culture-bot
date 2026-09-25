"""add pushkin_card to users

Revision ID: abfa3531555d
Revises: c927e9016e32
Create Date: 2026-09-26 01:54:33.475964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'abfa3531555d'
down_revision: Union[str, Sequence[str], None] = 'c927e9016e32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('pushkin_card', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'pushkin_card')
