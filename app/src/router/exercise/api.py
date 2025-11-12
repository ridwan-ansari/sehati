from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.session import get_async_session
from app.src.core.security import AuthService
from app.src.utils.handler import response_handler
from app.src.router.exercise.schema import ExerciseAnswerRequest
from app.src.router.exercise.crud import crud_exercise_habit_answer, crud_exercise_habit_question


router = APIRouter()
auth_service = AuthService()


@router.get("/questions")
async def get_exercise_questions(session: AsyncSession = Depends(get_async_session)):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Exercise habit questions retrieved successfully."
        response.data = await crud_exercise_habit_question.get_all_questions(session=session)
    return response.build()


@router.post("/answers")
async def submit_exercise_answers(
    payload: ExerciseAnswerRequest,
    session: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        user_id = auth["id"]
        answers_data = [item.model_dump() for item in payload.data]

        await crud_exercise_habit_answer.bulk_create_answers(
            session=session,
            user_id=user_id,
            answers=answers_data,
        )
        response.status_code = 201
        response.message = "Exercise habit answers submitted successfully."
    return response.build()
