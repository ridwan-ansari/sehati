from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.professionals import Professional, Appointment

class CRUDProfessional:
    async def list_professionals(self, session: AsyncSession):
        result = await session.execute(
            select(Professional).where(Professional.is_active == True)
        )
        return result.scalars().all()


class CRUDAppointment:
    async def create_appointment(self, session: AsyncSession, data: dict):
        ap = Appointment(**data)
        session.add(ap)
        await session.commit()
        await session.refresh(ap)
        return ap

    async def list_by_user(self, session: AsyncSession, user_id: str):
        result = await session.execute(
            select(Appointment)
            .where(Appointment.user_id == user_id)
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .options(
                selectinload(Appointment.professional)
            )
        )
        return result.scalars().all()

    async def get_detail(self, session: AsyncSession, appointment_id: str, user_id: str):
        result = await session.execute(
            select(Appointment)
            .where(
                Appointment.id == appointment_id,
                Appointment.user_id == user_id
            )
            .options(
                selectinload(Appointment.professional)
            )
        )
        return result.scalar_one_or_none()
