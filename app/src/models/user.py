from __future__ import annotations

from typing import List
from sqlalchemy import func, Enum
from sqlalchemy.orm import Mapped
from datetime import datetime, date
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from app.src.core.session import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fullname: Mapped[str] = mapped_column(index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    picture: Mapped[str] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
    verified: Mapped[bool] = mapped_column(default=False)
    date_of_birth: Mapped[date] = mapped_column(nullable=True)
    phone_number: Mapped[str] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(Enum("male", "female", name="gender_enum"))
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(Enum("admin", "user", name="role_enum"), default="user")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    user_nutritions: Mapped[List["UserNutrition"]] = relationship(back_populates="user")# type: ignore
