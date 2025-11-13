from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.session import get_async_session
from app.src.core.security import AuthService
from app.src.utils.handler import response_handler
from app.src.router.recipe.crud import CRUDRecipe

router = APIRouter()
auth_service = AuthService()


@router.get("/")
async def get_recipe(session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Recipe retrieved successfully."
        response.data = await CRUDRecipe().get_all(session=session)
    return response.build()