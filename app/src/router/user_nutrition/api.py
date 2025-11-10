from __future__ import annotations

from datetime import date
from fastapi import Depends, APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.router.user.crud import CRUDUser
from app.src.core.security import AuthService
from app.src.utils.handler import response_handler
from app.src.core.session import get_async_session
from app.src.models.user_nutrition import UserNutrition
from app.src.router.user_nutrition.crud import CRUDUserNutrition
from app.src.utils.nutrition_calculator import NutritionCalculator
from app.src.router.user_nutrition.schema import UserNutrionBaseModel

router = APIRouter()


@router.get("/")
async def get_list(
        limit: int = None,
        offset: int = None,
        session: AsyncSession = Depends(get_async_session),
        authentication: dict = Depends(AuthService().require_access_token)
    ):
    with response_handler() as response:
        response.status_code = 200
        response.message = "Get List User Successfully"
        response.data = await CRUDUserNutrition().get_list(session=session, user_id=authentication.get("id"), limit=limit, offset=offset)
    return response.build()

@router.post("/")
async def create(
        user_nutrition: UserNutrionBaseModel,
        session: AsyncSession = Depends(get_async_session),
        authentication: dict = Depends(AuthService().require_access_token)
    ):
    with response_handler() as response:
        calculator = NutritionCalculator(session=session)
        user = await CRUDUser().get_user_by_id(session=session, id=authentication.get("id"))

        result = await calculator.evaluate(
            gender=user.gender, 
            dob=user.date_of_birth, 
            weight=user_nutrition.weight_kg, 
            height=user_nutrition.height_cm
        )
        
        response.data = await CRUDUserNutrition().create(
            session=session, 
            user_nutrition=UserNutrition(**{
                    **user_nutrition.model_dump(),
                    "user_id":user.id,
                    "bmi":result.get(""),
                    "status":result.get("status"),
                    "ideal_weight_kg":result.get("ibw")   
                }
            )
        )
        response.status_code = 201
        response.message = "Create Successfully."
    return response.build()

@router.post("/calculator")
async def nutrition_calculator(
    dob: date = Form(...),
    gender: str = Form(...),
    weight: float = Form(...),
    height: float = Form(...),
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(AuthService().require_access_token)
):
    with response_handler() as response:
        calculator = NutritionCalculator(session=session)
        response.status_code = 200
        response.message = "Successfully Calculate."
        response.data = await calculator.evaluate(gender, dob, weight, height)
    return response.build()
        
    
