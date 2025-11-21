from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.user_nutrition import UserNutrition


class CRUDUserNutrition:
    async def create(self, session: AsyncSession, user_nutrition: UserNutrition) -> UserNutrition:
        session.add(user_nutrition)
        await session.commit()
        await session.refresh(user_nutrition)
        return user_nutrition

    async def get_list(
        self,
        session: AsyncSession,
        user_id: int,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0
    ) -> List[UserNutrition]:
        stmt = (
            select(UserNutrition)
            .where(UserNutrition.user_id == user_id)
            .order_by(UserNutrition.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_latest(
        self,
        session: AsyncSession,
        user_id: int
    ) -> Optional[UserNutrition]:
        stmt = (
            select(UserNutrition)
            .where(UserNutrition.user_id == user_id)
            .order_by(UserNutrition.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_sorted(self, session, user_id, limit, offset, ordering):
        stmt = (
            select(UserNutrition)
            .where(UserNutrition.user_id == user_id)
            .order_by(ordering)
            .limit(limit).offset(offset)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count_by_user(self, session: AsyncSession, user_id: str):
        result = await session.execute(
            select(func.count()).select_from(UserNutrition).where(UserNutrition.user_id == user_id)
        )
        return result.scalar() or 0
