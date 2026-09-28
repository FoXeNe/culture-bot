"""add geo to users and events

Revision ID: 3f1a8c2d4e7b
Revises: abfa3531555d
Create Date: 2026-09-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '3f1a8c2d4e7b'
down_revision: Union[str, Sequence[str], None] = 'abfa3531555d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('events', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('events', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'latitude')
    op.drop_column('users', 'longitude')
    op.drop_column('events', 'latitude')
    op.drop_column('events', 'longitude')
