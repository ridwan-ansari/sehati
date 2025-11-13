from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.core.security import AuthService
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
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
