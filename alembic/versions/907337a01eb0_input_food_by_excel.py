"""input food by excel

Revision ID: 907337a01eb0
Revises: bca70c66bff5
Create Date: 2025-11-19 08:35:01.420975

"""
import uuid
import pandas as pd
import sqlalchemy as sa

from alembic import op
from pathlib import Path
from datetime import datetime, timezone
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '907337a01eb0'
down_revision: Union[str, Sequence[str], None] = 'bca70c66bff5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    excel_path = Path("app/data/food.xlsx")
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel not found: {excel_path}")

    # Load Excel
    df = pd.read_excel(excel_path)

    # Bersihkan data
    df = df.rename(columns={"cal": "calories", "name": "name"})
    df["name"] = df["name"].astype(str).str.strip()

    # Buang baris yg name = NaN atau "nan"
    df = df[df["name"].notna()]
    df = df[df["name"].str.lower() != "nan"]

    # Buang baris calories NaN
    df = df[df["calories"].notna()]

    # Cast numeric calories → int
    df["calories"] = df["calories"].astype(float).astype(int)

    now = datetime.now(timezone.utc)

    df.insert(0, "id", [str(uuid.uuid4()) for _ in range(len(df))])
    df["category"] = None
    df["unit"] = "kcal"
    df["created_at"] = now
    df["updated_at"] = None
    df["deleted_at"] = None

    # TRUNCATE table, optional
    conn.execute(sa.text("TRUNCATE TABLE foods RESTART IDENTITY CASCADE;"))

    insert_stmt = sa.text("""
        INSERT INTO foods (
            id, name, category, calories, unit,
            created_at, updated_at, deleted_at
        ) VALUES (
            :id, :name, :category, :calories, :unit,
            :created_at, :updated_at, :deleted_at
        )
    """)

    records = df.to_dict(orient="records")
    conn.execute(insert_stmt, records)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM foods;"))
