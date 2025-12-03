from typing import List
from fastapi import APIRouter, Depends
from app.src.core.security import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.reminder.crud import crud_reminder
from app.src.router.reminder.schema import (
    ReminderBase,
    ReminderUpdate,
    ReminderResponse
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
):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Reminder successfully created."
        response.data = await crud_reminder.get_by_user(session, authentication.get("id"), title, limit, offset)
    return response.build()

@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    data: ReminderBase, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        response.status_code = 201
        response.message = "Reminder successfully created."
        response.data = await crud_reminder.create(session, data, authentication.get("id"))
    return response.build()


@router.get("/{id}", response_model=ReminderResponse)
async def get_reminder(
    id: str, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        reminder = await crud_reminder.get_by_id(session, id, authentication.get("id"))
        if not reminder:
            raise ValueError("Reminder not found.")
        response.status_code = 200
        response.message = "Reminder retrieved successfully."
        response.data = reminder
    return response.build()

@router.put("/{id}", response_model=ReminderResponse)
async def update_reminder(
    id: str, 
    data: ReminderUpdate, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        reminder = await crud_reminder.update(session, id, data, authentication.get("id"))
        if not reminder:
            raise ValueError("Reminder not found.")
        response.status_code = 200
        response.message = "Reminder updated successfully."
        response.data = reminder
    return response.build()

@router.delete("/{id}")
async def delete_reminder(
    id: str, 
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        await crud_reminder.delete(session, id, authentication.get("id"))
        response.status_code = 200
        response.message = "Reminder deleted successfully"
    return response.build()