"""enum meal type

Revision ID: bca70c66bff5
Revises: bea543274892
Create Date: 2025-11-19 07:09:27.713834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bca70c66bff5'
down_revision: Union[str, Sequence[str], None] = 'bea543274892'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum values
    op.execute("ALTER TYPE meal_type_enum ADD VALUE IF NOT EXISTS 'morning_snack';")
    op.execute("ALTER TYPE meal_type_enum ADD VALUE IF NOT EXISTS 'afternoon_snack';")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL cannot remove ENUM values directly,
    # so downgrade is intentionally left empty or you can raise exception
    # to prevent accidental downgrade.
    raise Exception("Downgrade not supported for ENUM value removal.")
