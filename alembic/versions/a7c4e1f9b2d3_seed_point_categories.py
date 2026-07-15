"""seed point categories

Revision ID: a7c4e1f9b2d3
Revises: f3a1c9d2e6b4
Create Date: 2026-07-15 00:00:00.000000

Without this seed, every point-earning/spending endpoint (including login)
fails with "Point category configuration not found" on a fresh database,
since no admin UI exists to manage this table — see README.
"""
import uuid
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c4e1f9b2d3'
down_revision: Union[str, Sequence[str], None] = 'f3a1c9d2e6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIES = [
    ("login", "Daily Login", 5, "gain", 1),
    ("watch_video", "Watch Educational Video", 5, "gain", 1),
    ("admin_bonus", "Admin Bonus", 10, "gain", 1),
    ("food_diary", "Food Diary Submission", 10, "gain", 1),
    ("food_habit_answer", "DQQ Food Habit Answer", 10, "gain", 1),
    ("exercise_answer", "PAQ-A Exercise Answer", 10, "gain", 1),
    ("playing_game", "Claim Game", 10, "spend", 1),
    ("merchandise_redeem", "Redeem Merchandise", 10, "spend", 1),
    ("bodyweight_monitoring", "Bodyweight Monitoring", 5, "gain", 1),
    ("konseling_gizi", "Nutrition Counseling Appointment", 15, "gain", 1),
    ("konseling_psikolog", "Psychologist Counseling Appointment", 15, "gain", 1),
    ("forum_post", "Forum Post", 5, "gain", 1),
    ("chat_friend", "Chat with Friend", 5, "gain", 1),
    ("read_menu_sehat", "Read Healthy Recipe", 5, "gain", 1),
    ("set_reminder", "Set Reminder", 5, "gain", 1),
]


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    stmt = sa.text("""
        INSERT INTO point_categories (id, code, name, default_points, flow, daily_max, created_at)
        VALUES (:id, :code, :name, :default_points, :flow, :daily_max, :created_at)
        ON CONFLICT (code) DO NOTHING
    """)
    conn.execute(stmt, [
        {
            "id": str(uuid.uuid4()),
            "code": code,
            "name": name,
            "default_points": default_points,
            "flow": flow,
            "daily_max": daily_max,
            "created_at": now,
        }
        for code, name, default_points, flow, daily_max in CATEGORIES
    ])


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    codes = [code for code, *_ in CATEGORIES]
    conn.execute(
        sa.text("DELETE FROM point_categories WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
