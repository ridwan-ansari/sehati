from __future__ import annotations

from redis.asyncio import Redis
from app.src.core.config import settings

redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True, 
    username=settings.REDIS_USERNAME,
    password=settings.REDIS_PASSWORD
)
