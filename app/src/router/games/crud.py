from __future__ import annotations
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.models.games import Games


class CRUDGames:

    async def get_all(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ):
        stmt = (
            select(Games)
            .order_by(Games.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(self, session: AsyncSession) -> int:
        stmt = select(func.count(Games.id))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, session: AsyncSession, id: str):
        stmt = (
            select(Games)
            .where(Games.id == id)
            .options(selectinload(Games.claims))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create(self, session: AsyncSession, data: dict):
        new_game = Games(**data)
        session.add(new_game)
        await session.commit()
        await session.refresh(new_game)
        return new_game

    async def update(self, session: AsyncSession, id: str, data: dict):
        game = await self.get_by_id(session, id)
        if not game:
            return None

        for key, value in data.items():
            setattr(game, key, value)

        await session.commit()
        await session.refresh(game)
        return game

    async def delete(self, session: AsyncSession, id: str):
        game = await self.get_by_id(session, id)
        if not game:
            return False

        await session.delete(game)
        await session.commit()
        return True


crud_games = CRUDGames()
