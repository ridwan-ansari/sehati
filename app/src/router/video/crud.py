from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func
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
            .where(Video.deleted_at.is_(None), Video.is_active == True)
            .offset(offset)
            .limit(limit)
        )
        if title:
            stmt = stmt.where(Video.title.ilike(f"%{title}%"))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, id: str, session: AsyncSession) -> Optional[Video]:
        stmt = select(Video).where(Video.id == id, Video.deleted_at.is_(None))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self, session: AsyncSession, title: Optional[str] = None) -> int:
        stmt = select(func.count(Video.id)).where(Video.deleted_at.is_(None))
        if title:
            stmt = stmt.where(Video.title.ilike(f"%{title}%"))
        result = await session.execute(stmt)
        return result.scalar()

    async def get_all_admin(
        self,
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        title: Optional[str] = None,
    ) -> List[Video]:
        stmt = (
            select(Video)
            .where(Video.deleted_at.is_(None))
            .order_by(Video.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if title:
            stmt = stmt.where(Video.title.ilike(f"%{title}%"))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(self, session: AsyncSession, id: str, data: dict) -> Optional[Video]:
        video = await self.get_by_id(id=id, session=session)
        if not video:
            return None
        for key, value in data.items():
            setattr(video, key, value)
        await session.commit()
        await session.refresh(video)
        return video

    async def soft_delete(self, session: AsyncSession, id: str) -> bool:
        video = await self.get_by_id(id=id, session=session)
        if not video:
            return False
        video.deleted_at = datetime.now(timezone.utc)
        await session.commit()
        return True


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
        session: AsyncSession,
    ) -> Optional[VideoRewardClaim]:
        stmt = (
            select(VideoRewardClaim)
            .where(VideoRewardClaim.video_id == video_id, VideoRewardClaim.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


crud_video = CRUDVideo()
