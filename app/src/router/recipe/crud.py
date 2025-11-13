from __future__ import annotations
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.recipe import Recipe

class CRUDRecipe:
    async def get_all(self, session: AsyncSession, active_only: bool = True):
        stmt = select(Recipe)
        if active_only:
            stmt = stmt.where(Recipe.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalars().all()