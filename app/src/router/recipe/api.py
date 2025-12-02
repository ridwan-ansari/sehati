from __future__ import annotations
from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.point import CategoryCode
from app.src.core.security import AuthService
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.models.recipe import RecipeRewardClaim
from app.src.utils.point_service import reward_user_points
from app.src.router.recipe.crud import CRUDRecipe, CRUDRecipeRewardClaim

router = APIRouter()
crud_recipe = CRUDRecipe()
auth_service = AuthService()
crud_recipe_reward = CRUDRecipeRewardClaim()


@router.get("/")
async def get_recipe(
    name: str = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Recipe retrieved successfully."
        response.data = await crud_recipe.get_all(session=session, name=name, limit=limit, offset=offset)
    return response.build()


@router.post("/claim-point")
async def claim_point(
    recipe_id: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        user_id=authentication.get("id")
        recipe = await crud_recipe.get_by_id(session=session, id=recipe_id)
        if not recipe:
            raise ValueError("Recipe not found.")
        
        reward = await crud_recipe_reward.is_claim(session=session, recipe_id=recipe_id, user_id=user_id)
        if not reward:
            await crud_recipe_reward.create(session=session, recipe_reward_claim=RecipeRewardClaim(**{"recipe_id":recipe.id, "user_id":user_id}))
            await reward_user_points(session=session, user_id=user_id, category=CategoryCode.read_menu_sehat)
        response.status_code = 201
        response.message = "Congratulation, successfully reward claim."
    return response.build()