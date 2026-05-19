from __future__ import annotations

import jwt
from fastapi import Depends
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.src.core.config import settings
from app.src.utils.i18n import get_lang, t
from app.src.utils.execeptions import UnauthorizedException, ForbiddenException

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenService:
    def __init__(self):
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY

    def generate_token(
        self,
        payload: dict,
        token_type: str = "access",
        expires_in_hours: float | None = None,
        expires_in_minutes: float | None = None,
    ) -> str:
        default_expiry = {
            "access": timedelta(minutes=15),
            "refresh": timedelta(days=30),
            "reset_password": timedelta(minutes=10),
        }

        if expires_in_hours is not None:
            expires = timedelta(hours=expires_in_hours)
        elif expires_in_minutes is not None:
            expires = timedelta(minutes=expires_in_minutes)
        else:
            expires = default_expiry.get(token_type, timedelta(minutes=15))

        to_encode = payload.copy()
        to_encode.update({
            "type": token_type,
            "exp": datetime.now(timezone.utc) + expires,
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


class AuthService:
    def __init__(self):
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY

    async def _decode_token(self, token: str, lang: str = "en") -> dict:
        try:
            return jwt.decode(
                jwt=token,
                key=self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True
                }
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(t("token_expired", lang))
        except jwt.InvalidTokenError:
            raise UnauthorizedException(t("token_malformed", lang))
        except Exception as e:
            raise UnauthorizedException(t("token_validation_failed", lang, error=str(e)))

    async def require_access_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        lang: str = Depends(get_lang),
    ) -> dict:
        payload = await self._decode_token(credentials.credentials, lang)
        if payload.get("type") != "access":
            raise UnauthorizedException(t("access_token_invalid", lang))
        return payload

    async def require_refresh_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        lang: str = Depends(get_lang),
    ) -> dict:
        payload = await self._decode_token(credentials.credentials, lang)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(t("refresh_token_invalid", lang))
        return payload

    async def require_access_admin(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        lang: str = Depends(get_lang),
    ) -> dict:
        payload = await self._decode_token(credentials.credentials, lang)
        if payload.get("type") != "access" or payload.get("role") != "admin":
            raise ForbiddenException(t("admin_access_required", lang))
        return payload


class Hasher:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)