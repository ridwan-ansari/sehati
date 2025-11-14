from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler

from app.src.router.sleep.schema import SleepCreateSchema, SleepResponseSchema
from app.src.router.sleep.crud import sleep_crud

router = APIRouter()
auth_service = AuthService()


@router.post("/", status_code=201)
async def create_sleep_record(
    data: SleepCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:

        record = await sleep_crud.create(
            session=session,
            user_id=authentication["id"],
            start_time=data.start_time,
            wake_up_time=data.wake_up_time,
            target_sleep_minutes=data.target_sleep_minutes,
        )

        response.status_code = 201
        response.message = "Sleep record created successfully."
        response.data = SleepResponseSchema.model_validate(record)
        return response.build()


@router.get("/", status_code=200)
async def list_sleep_records(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:

        records = await sleep_crud.get_by_user(
            session=session,
            user_id=authentication["id"],
            limit=limit,
            offset=offset
        )

        data = []
        for r in records:
            hours = round(r.sleep_duration_minutes / 60, 2)
            target_hours = round(r.target_sleep_minutes / 60, 2)

            item = SleepResponseSchema.model_validate({
                **r.__dict__,
                "sleep_duration_hours": hours,
                "target_sleep_hours": target_hours
            })
            data.append(item)

        response.status_code = 200
        response.message = "Sleep records fetched successfully."
        response.data = data
        return response.build()
