from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import String, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class ExerciseHabitQuestion(Base, TimestampMixin):
    __tablename__ = "exercise_habit_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(String, nullable=False)
    example: Mapped[str | None] = mapped_column(String, nullable=True)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    question_type: Mapped[str] = mapped_column(String(50), default="multiple_choice", nullable=False)
    order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reward_points: Mapped[int] = mapped_column(default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    answers = relationship("ExerciseHabitAnswer", back_populates="question", cascade="all, delete-orphan")


class ExerciseHabitAnswer(Base, TimestampMixin):
    __tablename__ = "exercise_habit_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("exercise_habit_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option: Mapped[str | None] = mapped_column(String(50), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(String, nullable=True)
    recorded_at: Mapped[date] = mapped_column(default=date.today, nullable=False)

    user = relationship("User", back_populates="exercise_habit_answers")
    question = relationship("ExerciseHabitQuestion", back_populates="answers")
