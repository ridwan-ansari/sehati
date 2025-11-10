from __future__ import annotations

from typing import List
from pydantic import BaseModel


class FoodHabitAnswerSchema(BaseModel):
    question_id: str
    answer: bool
    frequency: int = 0

class UserAnswer(BaseModel):
    answers: List[FoodHabitAnswerSchema]