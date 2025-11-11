from __future__ import annotations
from typing import List, Optional
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.user import User
from app.src.core.security import AuthService
from app.src.router.user.crud import CRUDUser
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.user.schema import UserBaseModel, UserProfile

router = APIRouter()
crud_user = CRUDUser()
auth_service = AuthService()


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

@router.get("/profile")
async def profile(
    authentication: dict = Depends(auth_service.require_access_token),
    session: AsyncSession = Depends(get_async_session)
):
    user = await crud_user.get_user_by_id(session=session, id=authentication.get("id"))
    with response_handler() as response:
        response.status_code = 200
        response.message = "Get Profile Successfully."
        response.data = UserProfile.model_validate(user)
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
