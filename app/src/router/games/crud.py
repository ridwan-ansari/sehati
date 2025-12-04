from __future__ import annotations
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased

from app.src.models.games import Games, GameClaim


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
    
    async def get_all_with_claim_status(
        self,
        session: AsyncSession,
        user_id: str,
        name: str = None,
        limit: int = 20,
        offset: int = 0
    ):

        UserClaim = aliased(GameClaim)

        stmt = (
            select(
                Games,
                case(
                    (UserClaim.id.is_not(None), True),
                    else_=False
                ).label("is_claim")
            )
            .outerjoin(
                UserClaim,
                (UserClaim.game_id == Games.id) &
                (UserClaim.user_id == user_id) &
                (UserClaim.deleted_at.is_(None))
            )
            .where(
                Games.deleted_at.is_(None),
            )
            .order_by(Games.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if name:
            stmt = stmt.where(Games.name.ilike(f"%{name}%"))

        result = await session.execute(stmt)
        return result.all()


class CRUDGameClaim:

    async def create(self, session: AsyncSession, data: dict):
        claim = GameClaim(**data)
        session.add(claim)
        await session.commit()
        await session.refresh(claim)
        return claim

    async def get_by_id(self, session: AsyncSession, id: str):
        stmt = (
            select(GameClaim)
            .where(GameClaim.id == id)
            .options(selectinload(GameClaim.user))
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_game_user_id(self, session: AsyncSession, game_id: str, user_id):
        stmt = (
            select(GameClaim)
            .where(GameClaim.game_id == game_id, GameClaim.user_id == user_id)
            .options(selectinload(GameClaim.user), selectinload(GameClaim.game))
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
crud_games = CRUDGames()
