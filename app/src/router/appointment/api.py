from loguru import logger
from fastapi import APIRouter, Depends
from app.src.core.security import AuthService
from app.src.models.point import CategoryCode 
from app.src.router.user.crud import crud_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.utils.email_client import email_client
from app.src.utils.point_service import reward_user_points
from app.src.router.appointment.schema import AppointmentCreateSchema
from app.src.router.appointment.crud import CRUDProfessional, CRUDAppointment

router = APIRouter()
crud_app = CRUDAppointment()
auth_service = AuthService()
crud_prof = CRUDProfessional()

@router.get("/professionals")
async def list_professionals(
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        data = await crud_prof.list_professionals(session)
        response.data = data
        response.message = "Professionals fetched"
    return response.build()

@router.post("/")
async def create_appointment(
    data: AppointmentCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        user_id = authentication.get("id")
        user = await crud_user.get_user_by_id(session=session, id=user_id)
        prof = await crud_prof.get_by_id(session=session, id=data.professional_id)

        if not prof:
            raise ValueError("Doctor not found.")
        
        if prof.specialization == "Nutritionist/Dietitian" and not await crud_app.exists_this_week(session=session, user_id=user_id, professional_id=prof.id):
            await reward_user_points(session=session, user_id=user_id, category=CategoryCode.konseling_gizi)
        elif prof.specialization == "Psychologist" and not await crud_app.exists_this_month(session=session, user_id=user_id, professional_id=prof.id):
            await reward_user_points(session=session, user_id=user_id, category=CategoryCode.konseling_psikolog)
        
        ap = await crud_app.create_appointment(
            session=session,
            data={
                "user_id": authentication["id"],
                "professional_id": data.professional_id,
                "appointment_date": data.appointment_date,
                "appointment_time": data.appointment_time,
                "notes": data.notes
            }
        )

        try:
            email_client.send_appointment(recipient=prof.email, context={
                "doctor_name":prof.fullname, 
                "fullname":user.fullname, 
                "email":user.email, 
                "appointment_date":f"{data.appointment_date} - {data.appointment_time}"
                }
            )
        except Exception as error:
            logger.error(error)
        response.data = {"id": ap.id}
        response.message = "Appointment created"
    return response.build()

@router.get("/")
async def list_user_appointments(
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        data = await crud_app.list_by_user(session, authentication["id"])
        response.data = data
        response.message = "Appointments fetched"
    return response.build()

@router.get("/{appointment_id}")
async def appointment_detail(
    appointment_id: str,
    session: AsyncSession = Depends(get_async_session),
    authentication: dict = Depends(auth_service.require_access_token)
):
    with response_handler() as response:
        detail = await crud_app.get_detail(session, appointment_id, authentication["id"])
        response.data = detail
        response.message = "Appointment detail"
    return response.build()
