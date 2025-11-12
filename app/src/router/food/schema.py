from __future__ import annotations

from typing import List
from pydantic import BaseModel


class FoodHabitAnswerSchema(BaseModel):
    question_id: str
    answer: bool
    frequency: int = 0


class UserAnswer(BaseModel):
    answers: List[FoodHabitAnswerSchema]


class FoodDiaryItem(BaseModel):
    food_id: str
    meal_type: str
    quantity: int = 1


class FoodDiarySchema(BaseModel):
    activity: str
    desired_energy_requirement: int
    data: List[FoodDiaryItem]
