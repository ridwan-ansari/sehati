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
    SMTP_IS_SSL: bool = True
    MEDIA_ROOT: str = "/var/sehati-media"
    MEDIA_URL: str = "/media"
    MAX_AVATAR_MB: int = 2
    PASSWORD_REGEX: str = r"^(?=.*[A-Za-z])(?=.*\d).{8,}$"

settings = Settings(_env_file='.env')