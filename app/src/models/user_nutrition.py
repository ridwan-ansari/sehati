from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import relationship
from app.src.core.session import Base


class UserNutrition(Base):
    __tablename__ = 'user_nutritions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    bmi: Mapped[float] = mapped_column(nullable=True)
    height_cm: Mapped[float] = mapped_column(nullable=True)
    weight_kg: Mapped[float] = mapped_column(nullable=True)
    ideal_weight_kg: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    user: Mapped['User'] = relationship(back_populates="user_nutritions")# type: ignore
