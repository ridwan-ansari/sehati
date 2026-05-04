from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.utils.i18n import get_lang, t
from app.src.router.sleep.schema import SleepCreateSchema, SleepResponseSchema
from app.src.router.sleep.crud import sleep_crud

router = APIRouter()
auth_service = AuthService()


@router.post("/", status_code=201)
async def create_sleep_record(
    data: SleepCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        if data.wake_up_time <= data.sleep_time:
            raise ValueError(t("sleep_time_invalid", lang))

        record = await sleep_crud.create(
            session=session,
            user_id=authentication["id"],
            sleep_time=data.sleep_time,
            wake_up_time=data.wake_up_time,
            target_sleep_hours=data.target_sleep_hours,
            lang=lang,
        )
        response.status_code = 201
        response.message = t("sleep_created_success", lang)
        response.data = SleepResponseSchema(
            id=record.id,
            sleep_time=record.sleep_time,
            wake_up_time=record.wake_up_time,
            sleep_duration_minutes=record.sleep_duration_minutes,
            sleep_duration_hours=round(record.sleep_duration_minutes / 60, 2),
            target_sleep_hours=record.target_sleep_hours,
            created_at=record.created_at,
        )
    return response.build()


@router.get("/", status_code=200)
async def list_sleep_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        records = await sleep_crud.get_by_user(
            session=session, user_id=authentication["id"], limit=limit, offset=offset
        )
        total = await sleep_crud.get_total_by_user(session=session, user_id=authentication["id"])
        response.status_code = 200
        response.message = t("sleep_list_success", lang)
        response.data = [
            SleepResponseSchema(
                id=r.id,
                sleep_time=r.sleep_time,
                wake_up_time=r.wake_up_time,
                sleep_duration_minutes=r.sleep_duration_minutes,
                sleep_duration_hours=round(r.sleep_duration_minutes / 60, 2),
                target_sleep_hours=r.target_sleep_hours,
                created_at=r.created_at,
            )
            for r in records
        ]
        response.total = total
    return response.build()
