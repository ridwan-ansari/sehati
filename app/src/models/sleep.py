from __future__ import annotations
import uuid
from datetime import time
from sqlalchemy import String, ForeignKey, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin

class Sleep(Base, TimestampMixin):
    __tablename__ = "sleep_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    wake_up_time: Mapped[time] = mapped_column(Time, nullable=False)

    sleep_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    target_sleep_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="sleep_records")
