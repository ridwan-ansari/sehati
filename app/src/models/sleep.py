from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin

class Sleep(Base, TimestampMixin):
    __tablename__ = "sleep_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    sleep_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    wake_up_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    sleep_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    target_sleep_hours: Mapped[int] = mapped_column(Integer, nullable=True)

    user = relationship("User", back_populates="sleep_records")
    
    @property
    def actual_duration_minutes(self) -> int:
        return int((self.wake_up_time - self.sleep_time).total_seconds() / 60)
    
    @property
    def duration_difference_minutes(self) -> int:
        return self.actual_duration_minutes - self.target_sleep_minutes