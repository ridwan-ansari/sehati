from pydantic import BaseModel
from datetime import time

class SleepCreateSchema(BaseModel):
    start_time: time
    wake_up_time: time
    target_sleep_minutes: int

class SleepResponseSchema(BaseModel):
    id: str
    start_time: time
    wake_up_time: time
    sleep_duration_minutes: int
    target_sleep_minutes: int
    sleep_duration_hours: float
    target_sleep_hours: float
    created_at: str

    class Config:
        from_attributes = True
