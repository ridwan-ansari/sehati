from __future__ import annotations
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.security import AuthService
from app.src.models.food import FoodHabitAnswer
from app.src.router.food.schema import UserAnswer
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.router.food.crud import (
    CRUDFood,
    CRUDFoodHabitAnswer,
    CRUDFoodHabitQuestion
)

router = APIRouter()
auth_service = AuthService()
crud_food = CRUDFood()
crud_habit_answer = CRUDFoodHabitAnswer()
crud_habit_question = CRUDFoodHabitQuestion()


@router.get("/food")
async def get_all_foods(
    name: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        foods = await crud_food.get_all(session=session, name=name, limit=limit, offset=offset)
        response.status_code = 200
        response.message = "Food list retrieved successfully."
        response.data = foods
    return response.build()


@router.get("/food/questions")
async def get_food_questions(
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        questions = await crud_habit_question.get_all(session=session)
        response.status_code = 200
        response.message = "Food habit questions retrieved successfully."
        response.data = questions
    return response.build()


@router.post("/food/answers")
async def submit_food_habit_answers(
    user_answers: UserAnswer,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
):
    with response_handler() as response:
        answers = [
            FoodHabitAnswer(**{
                **answer.model_dump(),
                "user_id": authentication.get("id"),
            })
            for answer in user_answers.answers
        ]
        created = await crud_habit_answer.bulk_create(session=session, answers=answers)
        response.status_code = 201
        response.message = "Food habit answers submitted successfully."
        response.data = created
    return response.build()
