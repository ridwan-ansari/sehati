from __future__ import annotations
from fastapi import APIRouter, Depends
from app.src.core.security import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.point.crud import CRUDPointWallet

router = APIRouter()
auth_service = AuthService()
crud_wallet = CRUDPointWallet()

@router.get("/leaderboard")
async def leaderboard(
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        wallets = await crud_wallet.get_all(session=session)

        data = [
            {
                "nickname": wallet.user.nickname,
                "achievement_points": wallet.achievement_points,
                "credit_points": wallet.credit_points
            }
            for wallet in wallets
        ]

        response.status_code = 200
        response.message = "Wallet ranking retrieved successfully."
        response.data = data

    return response.build()