from __future__ import annotations
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class UserNutrition(Base, TimestampMixin):
    __tablename__ = "user_nutritions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bmi: Mapped[float] = mapped_column(nullable=True)
    height_cm: Mapped[float] = mapped_column(nullable=True)
    weight_kg: Mapped[float] = mapped_column(nullable=True)
    ideal_weight_kg: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    type_of_activity: Mapped[str] = mapped_column(nullable=False)

    user = relationship("User", back_populates="user_nutritions")
