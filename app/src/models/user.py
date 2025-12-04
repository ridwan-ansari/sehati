from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fullname: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), index=True, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    picture: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    date_of_birth: Mapped[date | None]
    phone_number: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str] = mapped_column(Enum("male", "female", name="gender_enum"), nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(Enum("admin", "user", name="role_enum"), default="user", nullable=False)

    # --- Relationships ---
    user_nutritions = relationship("UserNutrition", back_populates="user", cascade="all, delete-orphan")
    chat_participants = relationship("ChatParticipant", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="sender", cascade="all, delete-orphan")
    point_wallet = relationship("PointWallet", back_populates="user", uselist=False)
    food_habit_answers = relationship("FoodHabitAnswer", back_populates="user", cascade="all, delete-orphan")
    food_diary_analysis = relationship("FoodDiaryAnalysis", back_populates="user", cascade="all, delete-orphan")
    exercise_habit_answers = relationship("ExerciseHabitAnswer", back_populates="user", cascade="all, delete-orphan")
    forum_posts = relationship("ForumPost", back_populates="user", cascade="all, delete-orphan")
    forum_comments = relationship("ForumComment", back_populates="user", cascade="all, delete-orphan")
    forum_likes = relationship("ForumLike", back_populates="user", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    sleep_records = relationship("Sleep", back_populates="user", cascade="all, delete-orphan")
    merchandise_claims = relationship("MerchandiseClaim", back_populates="user")
    game_claims = relationship("GameClaim", back_populates="user")
