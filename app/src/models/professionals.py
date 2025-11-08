from __future__ import annotations
import uuid
from datetime import date, time
from sqlalchemy import String, JSON, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Professional(Base, TimestampMixin):
    __tablename__ = "professionals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fullname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20))
    specialization: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    picture: Mapped[str | None] = mapped_column(String)
    available_days: Mapped[dict | None] = mapped_column(JSON)   # example: {"monday": True, "tuesday": False}
    available_hours: Mapped[dict | None] = mapped_column(JSON)  # example: {"start": "09:00", "end": "17:00"}
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    appointments = relationship("Appointment", back_populates="professional", cascade="all, delete-orphan")


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    professional_id: Mapped[str] = mapped_column(ForeignKey("professionals.id", ondelete="CASCADE"))
    appointment_date: Mapped[date] = mapped_column(nullable=False)
    appointment_time: Mapped[time] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "confirmed", "completed", "cancelled", name="appointment_status_enum"),
        default="pending",
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    professional = relationship("Professional", back_populates="appointments")
    user = relationship("User")
