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
    
    async def get_all(self, session: AsyncSession, limit: int, offset: int):
        stmt = select(Recipe).limit(limit=limit).offset(offset=offset)
        result = await session.execute(stmt)
        return result.scalars().all()