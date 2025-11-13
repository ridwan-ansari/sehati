from pydantic import BaseModel
from datetime import date, time

class AppointmentCreateSchema(BaseModel):
    professional_id: str
    appointment_date: date
    appointment_time: time
    notes: str | None = None
