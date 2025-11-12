from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class UserNutrionBaseModel(BaseModel):
    height_cm: Optional[float]
    weight_kg: Optional[float]
