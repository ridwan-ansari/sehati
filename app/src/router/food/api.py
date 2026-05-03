from __future__ import annotations
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.router.user.crud import CRUDUser
from app.src.models.point import CategoryCode
from app.src.core.security import AuthService
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.utils.i18n import get_lang, t
from app.src.utils.point_service import reward_user_points
from app.src.models.food import FoodHabitAnswer, FoodDiaryItem
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.router.food.schema import UserAnswer, FoodDiarySchema
from app.src.utils.nutrition_calculator import NutritionCalculator
from app.src.router.food.crud import (
    CRUDFood,
    CRUDFoodDiaryItem,
    CRUDFoodHabitAnswer,
    CRUDFoodDiaryAnalysis,
    CRUDFoodHabitQuestion,
)

router = APIRouter()
crud_user = CRUDUser()
crud_food = CRUDFood()
auth_service = AuthService()
crud_nutrition = CRUDUserNutrition()
crud_diary_item = CRUDFoodDiaryItem()
crud_habit_answer = CRUDFoodHabitAnswer()
crud_diary_analysis = CRUDFoodDiaryAnalysis()
crud_habit_question = CRUDFoodHabitQuestion()


@router.get("/food")
async def get_all_foods(
    name: str | None = None,
    limit: int | None = 20,
    offset: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        foods = await crud_food.get_all(session=session, name=name, limit=limit, offset=offset)
        response.status_code = 200
        response.message = t("food_list_success", lang)
        response.data = foods
    return response.build()


@router.get("/food/questions")
async def get_food_questions(
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        questions = await crud_habit_question.get_all(session=session)
        response.status_code = 200
        response.message = t("food_questions_success", lang)
        response.data = questions
    return response.build()


@router.post("/food/answers")
async def submit_food_habit_answers(
    user_answers: UserAnswer,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        user_id = authentication["id"]
        if await crud_habit_answer.exists_today(session=session, user_id=user_id):
            raise ValueError(t("already_submitted_today", lang))
        answers = [
            FoodHabitAnswer(**{**answer.model_dump(), "user_id": user_id})
            for answer in user_answers.answers
        ]
        created = await crud_habit_answer.bulk_create(session=session, answers=answers)
        await reward_user_points(session=session, user_id=user_id, category=CategoryCode.food_habit_answer)
        response.status_code = 201
        response.message = t("food_answers_success", lang)
        response.data = created
    return response.build()


@router.post("/food/diary", status_code=201)
async def submit_food_diary(
    data: FoodDiarySchema,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        total_calories = 0
        user_id = authentication["id"]
        if await crud_diary_analysis.exists_today(session=session, user_id=user_id):
            raise ValueError(t("already_submitted_today", lang))
        user = await crud_user.get_user_by_id(session=session, id=user_id)
        user_nutrition = await crud_nutrition.get_latest(session=session, user_id=user_id)

        calculator = NutritionCalculator(session=session)
        energy = await calculator.evaluate(
            gender=user.gender,
            dob=user.date_of_birth,
            weight=user_nutrition.weight_kg,
            height=user_nutrition.height_cm,
            activity=data.activity,
        )

        for item in data.data:
            food = await crud_food.get_by_id(session=session, food_id=item.food_id)
            total_calories += item.weight_grams / 100 * food.calories * item.quantity

        diary_analysis = await crud_diary_analysis.create(
            session=session,
            data={
                "user_id": user_id,
                "energy_requirement": energy["eer"],
                "desired_energy_requirement": data.desired_energy_requirement,
                "total_calories": total_calories,
                "activity": data.activity,
            },
        )

        diary_items = [
            FoodDiaryItem(**item.model_dump(), food_diary_analysis_id=diary_analysis.id)
            for item in data.data
        ]
        await crud_diary_item.bulk_create(session=session, diary_items=diary_items)
        await reward_user_points(session=session, user_id=user_id, category=CategoryCode.food_diary)
        response.status_code = 201
        response.message = t("food_diary_success", lang)
    return response.build()


@router.get("/food/diary/analysis")
async def get_diary_analysis(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token),
    lang: str = Depends(get_lang),
):
    with response_handler() as response:
        response.status_code = 200
        response.message = t("diary_retrieved_success", lang)
        response.data = await crud_diary_analysis.get_by_user(
            session=session, user_id=authentication["id"], limit=limit, offset=offset
        )
    return response.build()
