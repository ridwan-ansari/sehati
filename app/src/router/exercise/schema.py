from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List


class ExerciseAnswerItem(BaseModel):
    question_id: str
    selected_option: Optional[str] = None
    answer_text: Optional[str] = None


class ExerciseAnswerRequest(BaseModel):
    data: List[ExerciseAnswerItem]