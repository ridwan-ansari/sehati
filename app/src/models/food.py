from __future__ import annotations
import uuid
from sqlalchemy import String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Food(Base, TimestampMixin):
    __tablename__ = "foods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    calories: Mapped[int] = mapped_column(default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="kcal", nullable=False)
    description: Mapped[str | None] = mapped_column(String)

    items = relationship("FoodDiaryItem", back_populates="food")


class FoodHabitQuestion(Base, TimestampMixin):
    __tablename__ = "food_habit_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(String, nullable=False)
    example: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    reward_points: Mapped[int] = mapped_column(default=10, nullable=False)

    answers = relationship("FoodHabitAnswer", back_populates="question", cascade="all, delete-orphan")


class FoodHabitAnswer(Base, TimestampMixin):
    __tablename__ = "food_habit_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[str] = mapped_column(ForeignKey("food_habit_questions.id", ondelete="CASCADE"))
    answer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    frequency: Mapped[int] = mapped_column(default=0)

    user = relationship("User", back_populates="food_habit_answers")
    question = relationship("FoodHabitQuestion", back_populates="answers")


class FoodDiaryAnalysis(Base, TimestampMixin):
    __tablename__ = "food_diary_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    energy_requirement: Mapped[int] = mapped_column(default=0)
    desired_energy_requirement: Mapped[int] = mapped_column(default=0)
    total_calories: Mapped[int] = mapped_column(default=0)
    reward_points: Mapped[int] = mapped_column(default=100, nullable=False)
    activity: Mapped[str] = mapped_column(nullable=False)

    user = relationship("User", back_populates="food_diary_analysis")
    items = relationship("FoodDiaryItem", back_populates="analysis", cascade="all, delete-orphan")


class FoodDiaryItem(Base, TimestampMixin):
    __tablename__ = "food_diary_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    food_diary_analysis_id: Mapped[str] = mapped_column(ForeignKey("food_diary_analysis.id", ondelete="CASCADE"))
    meal_type: Mapped[str] = mapped_column(Enum("breakfast", "lunch", "dinner", "morning_snack","afternoon_snack", name="meal_type_enum"))
    food_id: Mapped[str | None] = mapped_column(ForeignKey("foods.id", ondelete="SET NULL"))
    quantity: Mapped[int] = mapped_column(default=1)

    analysis = relationship("FoodDiaryAnalysis", back_populates="items")
    food = relationship("Food", lazy="joined")
