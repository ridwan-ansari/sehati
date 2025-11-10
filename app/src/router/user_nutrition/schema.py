from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class UserNutrionBaseModel(BaseModel):
    bmi: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    ideal_weight_kg: Optional[float] = None
    status: Optional[str] = None
    type_of_activity: Optional[str] = None