from typing import Optional
from sqlalchemy import select, and_
from datetime import date, timedelta
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.professionals import Professional, Appointment

class CRUDProfessional:
    async def list_professionals(self, session: AsyncSession):
        result = await session.execute(
            select(Professional).where(Professional.is_active == True)
        )
        return result.scalars().all()
    
    async def get_by_id(self, session: AsyncSession, id: str) -> Optional[Professional]:
        result = await session.execute(select(Professional).where(Professional.id == id))
        return result.scalar_one_or_none()


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

    async def exists_this_week(
        self,
        session: AsyncSession,
        user_id: str
    ):
        """Check if user has any appointment this week (Monday to Sunday)"""
        today = date.today()
        # Get Monday of current week
        start_of_week = today - timedelta(days=today.weekday())
        # Get Sunday of current week
        end_of_week = start_of_week + timedelta(days=6)
        
        stmt = (
            select(Appointment)
            .where(Appointment.user_id == user_id)
            .where(
                and_(
                    Appointment.appointment_date >= start_of_week,
                    Appointment.appointment_date <= end_of_week
                )
            )
            .limit(1)
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_this_month(
        self,
        session: AsyncSession,
        user_id: str
    ):
        """Check if user has any appointment this month"""
        today = date.today()
        # Get first day of current month
        start_of_month = date(today.year, today.month, 1)
        # Get last day of current month
        if today.month == 12:
            end_of_month = date(today.year, 12, 31)
        else:
            end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        stmt = (
            select(Appointment)
            .where(Appointment.user_id == user_id)
            .where(
                and_(
                    Appointment.appointment_date >= start_of_month,
                    Appointment.appointment_date <= end_of_month
                )
            )
            .limit(1)
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
