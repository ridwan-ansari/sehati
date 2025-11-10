from __future__ import annotations
import uuid
from sqlalchemy import String, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class BMIReference(Base, TimestampMixin):
    __tablename__ = "bmi_reference"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    age_months: Mapped[int] = mapped_column(Integer, nullable=False)

    sd_minus_3: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    sd_minus_2: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    sd_minus_1: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    median: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    sd_plus_1: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    sd_plus_2: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    sd_plus_3: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)

    __table_args__ = (
        UniqueConstraint("gender", "age_years", "age_months", name="uq_gender_age"),
    )
