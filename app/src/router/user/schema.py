from __future__ import annotations

import enum
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class GenderEnum(enum.Enum):
    male = 'male'
    female = 'female'


class UserBaseModel(BaseModel):
    fullname: str
    picture: Optional[str] = None
    nickname: Optional[str] = None

    @field_validator('fullname')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return v.upper()

    class Config:
        from_attributes = True


class UserProfile(UserBaseModel):
    email: EmailStr
    phone_number: Optional[str]
    gender: Optional[str] = None
    date_of_birth: Optional[date]

    class Config:
        from_attributes = True


class UserRegisterSchema(UserProfile):
    password: str
    
