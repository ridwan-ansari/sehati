from __future__ import annotations
from fastapi import Depends, APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.point import WalletKind
from app.src.core.security import AuthService
from app.src.models.video import VideoRewardClaim
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.point.crud import CRUDPointWallet, CRUDPointTransaction
from app.src.router.video.crud import CRUDVideo, CRUDVideoRewardClaim


router = APIRouter()
crud_video = CRUDVideo()
auth_service = AuthService()
crud_wallet = CRUDPointWallet()
crud_reward = CRUDVideoRewardClaim()
crud_point_transaction = CRUDPointTransaction()

@router.get("/")
async def get_videos(
    title: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Video list retrieved successfully."
        response.data = await crud_video.get_list(session=session, title=title, limit=limit, offset=offset)
    return response.build()

@router.post("/claim-reward")
async def claim_reward(
    video_id: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        video = await crud_video.get_by_id(session=session, id=video_id)
        if video:
            raise ValueError("Video not found.")
        
        reward = await crud_reward.get_by_user_id_video_id(session=session, video_id=video_id, user_id=auth.get("id"))
        if reward:
            raise ValueError("The reward has been claim.")
        
        reward = await crud_reward.create(session=session, video_reward_claim=VideoRewardClaim(**{"video_id":video_id, "user_id":auth.get("id")}))
        await crud_wallet.update_balance(session=session, user_id=auth.get("id"), wallet_type=WalletKind.achievement, amount=video.reward_points)

        response.status_code = 201
        response.message = "Congratulation, successfully reward claim."
    return response.build()