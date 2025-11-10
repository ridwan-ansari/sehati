from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from app.src.models.food import (
    Food,
    FoodHabitQuestion,
    FoodHabitAnswer,
    FoodDiaryAnalysis,
    FoodDiaryItem,
)
from typing import List, Optional


class CRUDFood:
    async def create(self, session: AsyncSession, **data) -> Food:
        food = Food(**data)
        session.add(food)
        await session.commit()
        await session.refresh(food)
        return food

    async def get_all(self, session: AsyncSession, name: str = None, limit: int = 20, offset: int = 0) -> List[Food]:
        stmt = (
            select(Food)
            .where(Food.deleted_at.is_(None))
            .limit(limit=limit)
            .offset(offset=offset)
        )
        
        if name:
            stmt = stmt.where(Food.name.ilike(f"%{name}%"))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, session: AsyncSession, food_id: str) -> Optional[Food]:
        result = await session.execute(select(Food).where(Food.id == food_id))
        return result.scalar_one_or_none()

    async def update(self, session: AsyncSession, food_id: str, **data) -> Optional[Food]:
        await session.execute(update(Food).where(Food.id == food_id).values(**data))
        await session.commit()
        return await self.get_by_id(session, food_id)

    async def delete(self, session: AsyncSession, food_id: str):
        await session.execute(delete(Food).where(Food.id == food_id))
        await session.commit()


class CRUDFoodHabitQuestion:
    async def create(self, session: AsyncSession, **data) -> FoodHabitQuestion:
        question = FoodHabitQuestion(**data)
        session.add(question)
        await session.commit()
        await session.refresh(question)
        return question

    async def get_all(self, session: AsyncSession, active_only: bool = True) -> List[FoodHabitQuestion]:
        stmt = select(FoodHabitQuestion)
        if active_only:
            stmt = stmt.where(FoodHabitQuestion.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, session: AsyncSession, question_id: str) -> Optional[FoodHabitQuestion]:
        result = await session.execute(select(FoodHabitQuestion).where(FoodHabitQuestion.id == question_id))
        return result.scalar_one_or_none()

    async def update(self, session: AsyncSession, question_id: str, **data) -> Optional[FoodHabitQuestion]:
        await session.execute(update(FoodHabitQuestion).where(FoodHabitQuestion.id == question_id).values(**data))
        await session.commit()
        return await self.get_by_id(session, question_id)

    async def delete(self, session: AsyncSession, question_id: str):
        await session.execute(delete(FoodHabitQuestion).where(FoodHabitQuestion.id == question_id))
        await session.commit()


class CRUDFoodHabitAnswer:
    async def create(self, session: AsyncSession, **data) -> FoodHabitAnswer:
        answer = FoodHabitAnswer(**data)
        session.add(answer)
        await session.commit()
        await session.refresh(answer)
        return answer

    async def get_by_user(self, session: AsyncSession, user_id: str) -> List[FoodHabitAnswer]:
        result = await session.execute(
            select(FoodHabitAnswer)
            .options(joinedload(FoodHabitAnswer.question))
            .where(FoodHabitAnswer.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_question(self, session: AsyncSession, question_id: str) -> List[FoodHabitAnswer]:
        result = await session.execute(select(FoodHabitAnswer).where(FoodHabitAnswer.question_id == question_id))
        return result.scalars().all()

    async def update(self, session: AsyncSession, answer_id: str, **data) -> Optional[FoodHabitAnswer]:
        await session.execute(update(FoodHabitAnswer).where(FoodHabitAnswer.id == answer_id).values(**data))
        await session.commit()
        return await self.get_by_id(session, answer_id)

    async def get_by_id(self, session: AsyncSession, answer_id: str) -> Optional[FoodHabitAnswer]:
        result = await session.execute(select(FoodHabitAnswer).where(FoodHabitAnswer.id == answer_id))
        return result.scalar_one_or_none()

    async def bulk_create(self, session: AsyncSession, answers: List[FoodHabitAnswer]):
        session.add_all(answers)
        await session.commit()
        return answers


class CRUDFoodDiaryAnalysis:
    async def create(self, session: AsyncSession, **data) -> FoodDiaryAnalysis:
        record = FoodDiaryAnalysis(**data)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def get_by_user(self, session: AsyncSession, user_id: str) -> List[FoodDiaryAnalysis]:
        result = await session.execute(
            select(FoodDiaryAnalysis)
            .options(joinedload(FoodDiaryAnalysis.items))
            .where(FoodDiaryAnalysis.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_id(self, session: AsyncSession, analysis_id: str) -> Optional[FoodDiaryAnalysis]:
        result = await session.execute(
            select(FoodDiaryAnalysis)
            .options(joinedload(FoodDiaryAnalysis.items))
            .where(FoodDiaryAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, session: AsyncSession, analysis_id: str):
        await session.execute(delete(FoodDiaryAnalysis).where(FoodDiaryAnalysis.id == analysis_id))
        await session.commit()


class CRUDFoodDiaryItem:
    async def create(self, session: AsyncSession, **data) -> FoodDiaryItem:
        item = FoodDiaryItem(**data)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def get_by_analysis(self, session: AsyncSession, analysis_id: str) -> List[FoodDiaryItem]:
        result = await session.execute(
            select(FoodDiaryItem)
            .options(joinedload(FoodDiaryItem.food))
            .where(FoodDiaryItem.food_diary_analysis_id == analysis_id)
        )
        return result.scalars().all()

    async def get_by_id(self, session: AsyncSession, item_id: str) -> Optional[FoodDiaryItem]:
        result = await session.execute(select(FoodDiaryItem).where(FoodDiaryItem.id == item_id))
        return result.scalar_one_or_none()

    async def update(self, session: AsyncSession, item_id: str, **data) -> Optional[FoodDiaryItem]:
        await session.execute(update(FoodDiaryItem).where(FoodDiaryItem.id == item_id).values(**data))
        await session.commit()
        return await self.get_by_id(session, item_id)

    async def delete(self, session: AsyncSession, item_id: str):
        await session.execute(delete(FoodDiaryItem).where(FoodDiaryItem.id == item_id))
        await session.commit()
