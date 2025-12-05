from __future__ import annotations
from fastapi import Depends, APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.dashboard.api import render_page
from app.src.utils.point_service import claim_games
from app.src.router.games.crud import crud_games, crud_game_claim

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

@router.get("/{game_id}/play")
async def play_game(
    game_id: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    claim = await crud_game_claim.get_by_game_user_id(session=session, game_id=game_id, user_id=authentication.get("id"))
    if not claim:
        raise ValueError("Something was wrong. Please contact administrator.")
    return render_page("admin/game.html", request, game=claim.game, auth=authentication)

@router.post("/{game_id}/claim")
async def user_claim_games(
    game_id: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        if not await crud_games.get_by_id(session=session, id=game_id):
            raise ValueError("Game not found.")
        claim = await crud_game_claim.get_by_game_user_id(session=session, game_id=game_id, user_id=authentication.get("id"))
        if not claim:
            await claim_games(session=session, user_id=authentication.get("id"), game_id=game_id)
        response.status_code = 200
        response.message = "Congratulations, the game has been claimed."
    return response.build()
        