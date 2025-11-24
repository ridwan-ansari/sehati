from __future__ import annotations
from datetime import date
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.exercise_habit import ExerciseHabitQuestion, ExerciseHabitAnswer


class CRUDExerciseHabitQuestion:
    async def get_all_questions(self, session: AsyncSession, active_only: bool = True):
        stmt = select(ExerciseHabitQuestion)
        if active_only:
            stmt = stmt.where(ExerciseHabitQuestion.is_active.is_(True))
        result = await session.execute(stmt.order_by(ExerciseHabitQuestion.order))
        return result.scalars().all()

    async def get_question_by_id(self, session: AsyncSession, question_id: str):
        stmt = select(ExerciseHabitQuestion).where(ExerciseHabitQuestion.id == question_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

class CRUDExerciseHabitAnswer:
    async def create_answer(
        self,
        session: AsyncSession,
        user_id: str,
        question_id: str,
        selected_option: str | None = None,
        answer_text: str | None = None,
    ):
        answer = ExerciseHabitAnswer(
            user_id=user_id,
            question_id=question_id,
            selected_option=selected_option,
            answer_text=answer_text,
        )
        session.add(answer)
        await session.commit()
        await session.refresh(answer)
        return answer

    async def bulk_create_answers(self, session: AsyncSession, user_id: str, answers: list[dict]):
        objects = [
            ExerciseHabitAnswer(
                user_id=user_id,
                question_id=item["question_id"],
                selected_option=item.get("selected_option"),
                answer_text=item.get("answer_text"),
            )
            for item in answers
        ]
        session.add_all(objects)
        await session.commit()
        return objects
    
    async def exists_today(
        self,
        session: AsyncSession,
        user_id: str
    ):
        stmt = (
            select(ExerciseHabitAnswer)
            .where(ExerciseHabitAnswer.user_id == user_id)
            .where(func.date(ExerciseHabitAnswer.created_at) == date.today())
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()


crud_exercise_habit_answer = CRUDExerciseHabitAnswer()
crud_exercise_habit_question = CRUDExerciseHabitQuestion()
