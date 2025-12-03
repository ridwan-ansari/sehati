from datetime import time
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


VALID_DAYS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}

class ReminderBase(BaseModel):
    title: Optional[str] = Field(None, example="Morning Medication")
    time: time = Field(..., example="07:30:00")  # type: ignore
    active: bool = Field(default=True, example=True)
    days: Optional[List[str]] = Field(
        None,
        example=["monday", "wednesday", "friday"]
    )
    message: Optional[str] = Field(None, example="Don't forget to take vitamin C")

    @field_validator("days")
    @classmethod
    def validate_days(cls, v):
        if v is None:
            return v
        normalized_days = []
        for item in v:
            day = item.lower()
            if day not in VALID_DAYS:
                raise ValueError(
                    f"Invalid day '{item}'. Allowed values: "
                    f"{', '.join(sorted(VALID_DAYS))}"
                )
            normalized_days.append(day)
        return normalized_days


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    time: Optional[time] = None # type: ignore
    active: Optional[bool] = None
    days: Optional[List[str]] = None
    message: Optional[str] = None


class ReminderResponse(ReminderBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True