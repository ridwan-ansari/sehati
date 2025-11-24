from __future__ import annotations
import os
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, APIRouter, UploadFile

from app.src.models.user import User
from app.src.core.config import settings
from app.src.core.security import AuthService
from app.src.router.user.crud import CRUDUser
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.point.crud import CRUDPointWallet
from app.src.router.user.schema import UserBaseModel, UserProfile
from app.src.utils.avatars import ensure_dir, read_limited, verify_image

router = APIRouter()
crud_user = CRUDUser()
auth_service = AuthService()
crud_wallet = CRUDPointWallet()
AVATAR_DIR = os.path.join(settings.MEDIA_ROOT, "avatars")


@router.get("/")
async def get_list(
    keyword: Optional[str] = None,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        users =  await crud_user.get_users(session=session, keyword=keyword, limit=limit, offset=offset)
        response.status_code = 200
        response.message = "Get List User Successfully."
        response.data = [UserBaseModel.model_validate(user) for user in users]
    return response.build()

@router.post("/profile/picture", status_code=201)
async def upload_profile_picture(
    file: UploadFile,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        ensure_dir("/var/sehati-media/avatars")

        if not file.content_type.startswith("image/"):
            raise ValueError("Only image files are allowed.")

        raw = await read_limited(file)
        verify_image(raw)

        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"

        filename = f"{uuid.uuid4()}{ext}"
        abs_path = os.path.join(AVATAR_DIR, filename)

        with open(abs_path, "wb") as f:
            f.write(raw)

        rel_path = f"avatars/{filename}"
        user = await crud_user.get_user_by_id(session=session, id=authentication["id"])
        user.picture = f"{settings.MEDIA_URL}/{rel_path}"
        await session.commit()

        response.status_code = 201
        response.message = "Profile picture updated."
        response.data = f"{settings.MEDIA_URL}/{rel_path}"


    return response.build()

@router.get("/profile")
async def profile(
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    user = await crud_user.get_user_by_id(session=session, id=authentication["id"])
    wallet = await crud_wallet.get_by_user(session=session, user_id=user.id)
    leaderboards = await crud_wallet.get_all(session=session)

    with response_handler() as response:
        profile_data = UserProfile.model_validate(user).model_dump()

        profile_data["achievement_points"] = wallet.achievement_points if wallet else 0
        profile_data["credit_points"] = wallet.credit_points if wallet else 0
        profile_data["rank"] = next(
            (index + 1 for index, w in enumerate(leaderboards) if w.user_id == user.id),
            None
        )

        response.status_code = 200
        response.message = "Get Profile Successfully."
        response.data = profile_data

    return response.build()

@router.get("/{id}")
async def profile(
    id: int,
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    user = await crud_user.get_user_by_id(session=session, id=id)
    with response_handler() as response:
        response.status_code = 200
        response.message = "Get User Successfully."
        response.data = UserProfile.model_validate(user)
    return response.build()
