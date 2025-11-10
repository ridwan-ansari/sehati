from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.video import Video, VideoRewardClaim


class CRUDVideo:
    async def create(self, session: AsyncSession, video: Video) -> Video:
        session.add(video)
        await session.commit()
        await session.refresh(video)
        return video

    async def get_list(
        self,
        session: AsyncSession,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        title: Optional[str] = None,
    ) -> List[Video]:
        stmt = (
            select(Video)
            .where(Video.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        if title:
            stmt = stmt.where(Video.title.ilike(f"%{title}%"))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, id: str, session: AsyncSession) -> Video:
        stmt = select(Video).where(Video.id.__eq__(id), Video.deleted_at.is_(None))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class CRUDVideoRewardClaim:
    async def create(self, session: AsyncSession, video_reward_claim: VideoRewardClaim) -> VideoRewardClaim:
        session.add(video_reward_claim)
        await session.commit()
        await session.refresh(video_reward_claim)
        return video_reward_claim
    
    async def get_by_user_id_video_id(
        self,
        video_id: str,
        user_id: str,
        session: AsyncSession
    )-> VideoRewardClaim:
        stmt = (
            select(VideoRewardClaim)
            .where(VideoRewardClaim.video_id.__eq__(video_id), VideoRewardClaim.user_id.__eq__(user_id))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
