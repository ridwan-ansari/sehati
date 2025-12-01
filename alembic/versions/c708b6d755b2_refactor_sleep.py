"""refactor sleep

Revision ID: c708b6d755b2
Revises: 330d490c24af
Create Date: 2025-12-01 07:09:18.088760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c708b6d755b2'
down_revision: Union[str, Sequence[str], None] = '330d490c24af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        ALTER TABLE sleep_records 
        RENAME COLUMN start_time TO sleep_time
    """)
    
    op.execute("""
        ALTER TABLE sleep_records 
        ALTER COLUMN sleep_time TYPE TIMESTAMP WITH TIME ZONE 
        USING (CURRENT_DATE + sleep_time)::TIMESTAMP WITH TIME ZONE
    """)
    
    op.execute("""
        ALTER TABLE sleep_records 
        ALTER COLUMN wake_up_time TYPE TIMESTAMP WITH TIME ZONE 
        USING (
            CASE 
                WHEN wake_up_time < sleep_time::TIME 
                THEN (CURRENT_DATE + INTERVAL '1 day' + wake_up_time)::TIMESTAMP WITH TIME ZONE
                ELSE (CURRENT_DATE + wake_up_time)::TIMESTAMP WITH TIME ZONE
            END
        )
    """)
    
    op.alter_column('sleep_records', 'sleep_duration_minutes',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('sleep_records', 'target_sleep_minutes',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        ALTER TABLE sleep_records 
        ALTER COLUMN sleep_time TYPE TIME 
        USING sleep_time::TIME
    """)
    
    op.execute("""
        ALTER TABLE sleep_records 
        ALTER COLUMN wake_up_time TYPE TIME 
        USING wake_up_time::TIME
    """)
    
    op.execute("""
        ALTER TABLE sleep_records 
        RENAME COLUMN sleep_time TO start_time
    """)
    
    op.alter_column('sleep_records', 'target_sleep_minutes',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('sleep_records', 'sleep_duration_minutes',
               existing_type=sa.INTEGER(),
               nullable=False)