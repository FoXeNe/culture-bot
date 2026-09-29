"""add frozen_week to users

Revision ID: b7e1f2a3c4d5
Revises: abfa3531555d
Create Date: 2026-09-30 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b7e1f2a3c4d5'
down_revision: Union[str, Sequence[str], None] = 'abfa3531555d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('frozen_week', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'frozen_week')
