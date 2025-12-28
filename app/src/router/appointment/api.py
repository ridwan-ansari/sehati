from loguru import logger
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Request, HTTPException

from app.src.router.user.crud import crud_user
from app.src.models.point import CategoryCode 
from app.src.core.templates import get_templates
from app.src.core.session import get_async_session
from app.src.utils.handler import response_handler
from app.src.utils.email_client import email_client
from app.src.utils.point_service import reward_user_points
from app.src.core.security import AuthService, TokenService
from app.src.router.appointment.schema import AppointmentCreateSchema
from app.src.router.appointment.crud import CRUDProfessional, CRUDAppointment

router = APIRouter()
templates = get_templates()
crud_app = CRUDAppointment()
auth_service = AuthService()
token_service = TokenService()
crud_prof = CRUDProfessional()

APPOINTMENT_TYPE = "appointment"
VALID_STATUSES = ["confirmed", "rejected"]

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

        code = token_service.generate_token(payload={"id":ap.id}, token_type="appointment")

        try:
            email_client.send_appointment(recipient=prof.email, context={
                "doctor_name":prof.fullname, 
                "fullname":user.fullname, 
                "email":user.email, 
                "phone_number": user.phone_number,
                "appointment_date":f"{data.appointment_date} - {data.appointment_time}",
                "confirm_url":f"https://sehatiapps.web.id/api/appointment/approved/{code}",
                "reject_url":f"https://sehatiapps.web.id/api/appointment/rejected/{code}"
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

@router.get("/{status}/{code}")
async def update_appointment_status(
    code: str,
    status: Literal["confirmed", "rejected"],
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        token_data = await auth_service._decode_token(code)
        
        if token_data.get("type") != APPOINTMENT_TYPE:
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        appointment_id = token_data.get("id")
        if not appointment_id:
            raise HTTPException(status_code=400, detail="Appointment ID not found")
        
        appointment = await crud_app.get_by_id(session=session, id=appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        if appointment.status in VALID_STATUSES:
            return templates.TemplateResponse(
                "errors/already_processed.html",
                {"request": request, "status": appointment.status},
                status_code=400
            )
        
        professional = await crud_prof.get_by_id(session=session, id=appointment.professional_id)
        user = await crud_user.get_user_by_id(session=session, id=appointment.user_id)
        
        if not professional or not user:
            raise HTTPException(status_code=404, detail="Professional or user not found")
        
        await crud_app.update_status_to_confirm(session=session, id=appointment_id, status=status)
        
        await email_client.send_mail(
            subject=f"SEHATI — Appointment {status.title()}",
            template_name="confirmed/appointment_status.html",
            recipient=user.email,
            context={
                "status": status,
                "appointment_date": appointment.appointment_date.strftime("%d %B %Y"),
                "appointment_time": appointment.appointment_time,
                "doctor_name": professional.fullname,
                "phone_number": professional.phone_number,
            }
        )
        
        return templates.TemplateResponse(
            "confirmed/appoint_confirmed.html",
            {"request": request, "status": status},
            status_code=200
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request},
            status_code=500
        )
