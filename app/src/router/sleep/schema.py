from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class SleepCreateSchema(BaseModel):
    sleep_time: datetime = Field(..., description="Waktu mulai tidur")
    wake_up_time: datetime = Field(..., description="Waktu bangun tidur")
    target_sleep_hours: int = Field(..., gt=7, description="Target durasi tidur dalam jam")


class SleepResponseSchema(BaseModel):
    id: str
    sleep_time: datetime
    wake_up_time: datetime
    sleep_duration_minutes: int
    sleep_duration_hours: float
    target_sleep_hours: float
    created_at: datetime

    class Config:
        from_attributes = True
