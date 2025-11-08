from __future__ import annotations
import uuid
from datetime import time
from sqlalchemy import String, Text, Time, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    active: Mapped[bool] = mapped_column(default=False)
    days: Mapped[list] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)

    user = relationship("User")
