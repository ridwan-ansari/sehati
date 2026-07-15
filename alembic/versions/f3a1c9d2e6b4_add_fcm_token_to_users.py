"""add fcm_token to users

Revision ID: f3a1c9d2e6b4
Revises: 8b30db692216
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d2e6b4'
down_revision: Union[str, Sequence[str], None] = '8b30db692216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('fcm_token', sa.String(length=255), nullable=True, comment='Firebase Cloud Messaging device token for push notifications'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'fcm_token')
