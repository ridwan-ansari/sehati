from __future__ import annotations
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.router.user.crud import CRUDUser
from app.src.core.security import AuthService
from app.src.router.games.crud import crud_games
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.point_service import redeem_merchandise_points

router = APIRouter()
auth_service = AuthService()


@router.get("/")
async def get_list(
    name: str = None, 
    limit: int = 20, 
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        data = await crud_games.get_all_with_claim_status(session=session, user_id=authentication.get("id"), name=name, limit=limit, offset=offset)
        response.data = [
            {
                "id": game.id,
                "name": game.name,
                "description": game.description,
                "image_url": game.image_url,
                "price_points": game.price_points,
                "is_claim": is_claim,
                "url": game.url if is_claim else None
            }
            for game, is_claim in data
        ]
        response.status_code = 200
        response.message = "Games retrieved successfully."
    return response.build()