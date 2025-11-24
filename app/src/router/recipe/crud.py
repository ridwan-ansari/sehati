from __future__ import annotations
from sqlalchemy import select, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.recipe import Recipe, RecipeRewardClaim

class CRUDRecipe:
    async def create(self, session: AsyncSession, data: dict):
        stmt = insert(Recipe).values(**data).returning(Recipe)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()
    
    async def get_all(self, session: AsyncSession, limit: int = None, offset: int = None):
        stmt = select(Recipe).limit(limit=limit).offset(offset=offset)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_id(self, session: AsyncSession, id: str):
        stmt = select(Recipe).where(Recipe.id.__eq__(id), Recipe.deleted_at.is_(None))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def count(self, session: AsyncSession) -> int:
        stmt = select(func.count()).select_from(Recipe)
        result = await session.execute(stmt)
        return result.scalar_one()

    
class CRUDRecipeRewardClaim:
    async def create(self, session: AsyncSession, recipe_reward_claim: RecipeRewardClaim) -> RecipeRewardClaim:
        session.add(recipe_reward_claim)
        await session.commit()
        await session.refresh(recipe_reward_claim)
        return recipe_reward_claim
    
    async def is_claim(
        self,
        user_id: str,
        recipe_id: str,
        session: AsyncSession
    )-> RecipeRewardClaim:
        stmt = (
            select(RecipeRewardClaim)
            .where(RecipeRewardClaim.recipe_id.__eq__(recipe_id), RecipeRewardClaim.user_id.__eq__(user_id))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
