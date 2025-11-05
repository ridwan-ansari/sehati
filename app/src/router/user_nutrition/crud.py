from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select
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
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
