from typing import List
from fastapi import APIRouter, Depends
from app.src.models.point import CategoryCode
from app.src.core.security import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.i18n import get_lang, t
from app.src.utils.point_service import reward_user_points
from app.src.router.reminder.crud import crud_reminder
from app.src.router.reminder.schema import (
    ReminderBase,
    ReminderUpdate,
    ReminderResponse,
)

router = APIRouter()
auth_service = AuthService()


@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(
    title: str = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        response.status_code = 200
        response.message = t("reminders_fetched", lang)
        response.data = await crud_reminder.get_by_user(session, authentication.get("id"), title, limit, offset)
    return response.build()


@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    data: ReminderBase,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        await reward_user_points(session=session, user_id=authentication.get("id"), category=CategoryCode.set_reminder)
        response.status_code = 201
        response.message = t("reminder_created", lang)
        response.data = await crud_reminder.create(session, data, authentication.get("id"))
    return response.build()


@router.get("/{id}", response_model=ReminderResponse)
async def get_reminder(
    id: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        reminder = await crud_reminder.get_by_id(session, id, authentication.get("id"))
        if not reminder:
            raise ValueError(t("reminder_not_found", lang))
        response.status_code = 200
        response.message = t("reminder_retrieved", lang)
        response.data = reminder
    return response.build()


@router.put("/{id}", response_model=ReminderResponse)
async def update_reminder(
    id: str,
    data: ReminderUpdate,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        reminder = await crud_reminder.update(session, id, data, authentication.get("id"))
        if not reminder:
            raise ValueError(t("reminder_not_found", lang))
        response.status_code = 200
        response.message = t("reminder_updated", lang)
        response.data = reminder
    return response.build()


@router.delete("/{id}")
async def delete_reminder(
    id: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        await crud_reminder.delete(session, id, authentication.get("id"))
        response.status_code = 200
        response.message = t("reminder_deleted", lang)
    return response.build()
