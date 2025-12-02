from __future__ import annotations
from fastapi import Depends, APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.point import CategoryCode
from app.src.core.security import AuthService
from app.src.models.video import VideoRewardClaim
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.point_service import reward_user_points
from app.src.router.video.crud import CRUDVideo, CRUDVideoRewardClaim


router = APIRouter()
crud_video = CRUDVideo()
auth_service = AuthService()
crud_reward = CRUDVideoRewardClaim()

@router.get("/")
async def get_videos(
    title: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Video list retrieved successfully."
        response.data = await crud_video.get_list(session=session, title=title, limit=limit, offset=offset)
    return response.build()

@router.post("/claim-point")
async def claim_point(
    video_id: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        user_id=authentication.get("id")
        video = await crud_video.get_by_id(session=session, id=video_id)
        if not video:
            raise ValueError("Video not found.")
        
        reward = await crud_reward.get_by_user_id_video_id(session=session, video_id=video_id, user_id=user_id)
        if not reward:
            await crud_reward.create(session=session, video_reward_claim=VideoRewardClaim(**{"video_id":video_id, "user_id":user_id}))
            await reward_user_points(session=session, user_id=user_id, category=CategoryCode.watch_video)
        response.status_code = 201
        response.message = "Congratulation, successfully reward claim."
    return response.build()