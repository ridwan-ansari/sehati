from __future__ import annotations
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.merchandise import Merchandise

class CRUDMerchandise:
    async def create(self, session: AsyncSession, data: dict):
        obj = Merchandise(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def get_all(self, session: AsyncSession, limit: int = 10, offset: int = 0):
        result = await session.execute(
            select(Merchandise)
            .order_by(Merchandise.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count(self, session: AsyncSession):
        result = await session.execute(select(func.count()).select_from(Merchandise))
        return result.scalar()

crud_merch = CRUDMerchandise()