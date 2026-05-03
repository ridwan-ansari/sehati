from __future__ import annotations
import os
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, APIRouter, UploadFile

from app.src.core.config import settings
from app.src.core.security import AuthService
from app.src.router.user.crud import CRUDUser
from app.src.router.user.schema import UserProfile
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.i18n import get_lang, t
from app.src.router.point.crud import CRUDPointWallet
from app.src.router.food.crud import crud_answer, crud_analysis
from app.src.router.exercise.crud import crud_exercise_habit_answer
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.utils.avatars import ensure_dir, read_limited, verify_image

router = APIRouter()
crud_user = CRUDUser()
auth_service = AuthService()
crud_wallet = CRUDPointWallet()
crud_nutrition = CRUDUserNutrition()
AVATAR_DIR = os.path.join(settings.MEDIA_ROOT, "avatars")


@router.get("/")
async def get_list(
    keyword: Optional[str] = None,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        users = await crud_user.get_users(
            session=session, keyword=keyword, limit=limit, offset=offset,
            user_id=authentication.get("id"),
        )
        response.status_code = 200
        response.message = t("user_list_success", lang)
        response.data = [
            {"id": u.id, "fullname": u.fullname, "picture": u.picture, "nickname": u.nickname}
            for u in users
        ]
    return response.build()


@router.post("/profile/picture", status_code=201)
async def upload_profile_picture(
    file: UploadFile,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        ensure_dir("/var/sehati-media/avatars")

        if not file.content_type.startswith("image/"):
            raise ValueError(t("image_only_allowed", lang))

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
        response.message = t("profile_picture_updated", lang)
        response.data = f"{settings.MEDIA_URL}/{rel_path}"
    return response.build()


@router.get("/profile")
async def profile(
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session),
    lang: str = Depends(get_lang),
):
    user = await crud_user.get_user_by_id(session=session, id=authentication["id"])
    wallet = await crud_wallet.get_by_user(session=session, user_id=user.id)
    leaderboards = await crud_wallet.get_all(session=session)

    with response_handler() as response:
        profile_data = UserProfile.model_validate(user).model_dump()
        profile_data["achievement_points"] = wallet.achievement_points if wallet else 0
        profile_data["credit_points"] = wallet.credit_points if wallet else 0
        profile_data["rank"] = next(
            (index + 1 for index, w in enumerate(leaderboards) if w.user_id == user.id), None
        )
        response.status_code = 200
        response.message = t("profile_success", lang)
        response.data = profile_data
    return response.build()


@router.get("/{id}")
async def get_user_by_id(
    id: str,
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session),
    lang: str = Depends(get_lang),
):
    user = await crud_user.get_user_by_id(session=session, id=id)
    with response_handler() as response:
        response.status_code = 200
        response.message = t("user_success", lang)
        response.data = UserProfile.model_validate(user)
    return response.build()


@router.get("/notification/reminder")
async def get_notification_reminder(
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        user_id = authentication.get("id")

        task_keys = []
        if not await crud_exercise_habit_answer.exists_today(session=session, user_id=user_id):
            task_keys.append("task_exercise_habit")
        if not await crud_answer.exists_today(session=session, user_id=user_id):
            task_keys.append("task_food_habit")
        if not await crud_analysis.exists_today(session=session, user_id=user_id):
            task_keys.append("task_food_diary")
        if not await crud_nutrition.exists_today(session=session, user_id=user_id):
            task_keys.append("task_self_monitoring")

        if task_keys:
            task_names = [t(k, lang) for k in task_keys]
            _and = t("conjunction_and", lang)
            if len(task_names) == 1:
                tasks_str = task_names[0]
            elif len(task_names) == 2:
                tasks_str = f"{task_names[0]} {_and} {task_names[1]}"
            else:
                tasks_str = ", ".join(task_names[:-1]) + f", {_and} {task_names[-1]}"
            message = t("incomplete_tasks", lang, tasks=tasks_str)
        else:
            message = t("all_tasks_complete", lang)

        response.data = message
        response.message = t("notification_success", lang)
        response.status_code = 200
    return response.build()
