from __future__ import annotations

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = ""
    DATABASE_URL: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_SENDER: str

settings = Settings(_env_file='.env')