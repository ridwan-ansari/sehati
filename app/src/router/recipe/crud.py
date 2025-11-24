from __future__ import annotations
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.recipe import Recipe

class CRUDRecipe:
    async def create(self, session: AsyncSession, data: dict):
        stmt = insert(Recipe).values(**data).returning(Recipe)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()
    
    async def get_all(self, session: AsyncSession, active_only: bool = True):
        stmt = select(Recipe)
        if active_only:
            stmt = stmt.where(Recipe.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalars().all()