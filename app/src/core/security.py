from __future__ import annotations

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from datetime import timedelta, datetime, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.src.core.config import settings
from app.src.utils.execeptions import UnauthorizedException, ForbiddenException

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenService:
    def __init__(self):
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY

    def generate_access_token(self, payload: dict, expires: timedelta = timedelta(minutes=15)):
        to_encode = payload.copy()
        to_encode.update({
            "type": "access",
            "exp": datetime.now(timezone.utc) + expires
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, payload: dict, expires: timedelta = timedelta(hours=3600)):
        to_encode = payload.copy()
        to_encode.update({
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + expires
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


class AuthService:
    def __init__(self):
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY

    async def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                jwt=token,
                key=self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": True}
            )
        except Exception:
            raise UnauthorizedException("Invalid or expired token")

    async def require_access_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> dict:
        payload = await self._decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid access token")
        return payload

    async def require_refresh_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> dict:
        payload = await self._decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")
        return payload
    
    async def require_access_admin(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> dict:
        payload = await self._decode_token(credentials.credentials)
        if payload.get("type") != "access" or payload.get("role") != "admin":
            raise ForbiddenException("Admin access required.")
        return payload



class Hasher:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)