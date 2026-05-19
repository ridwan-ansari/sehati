from typing import Optional
from datetime import date, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.src.models.user import User
from app.src.models.professionals import Professional, Appointment


DAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKDAY_TO_KEY = {i: key for i, key in enumerate(DAY_KEYS)}


def normalize_available_hours(available_hours: Optional[dict], available_days: Optional[dict]) -> dict:
    if not available_hours:
        return {}
    if any(d in available_hours and isinstance(available_hours[d], dict) for d in DAY_KEYS):
        return {
            d: available_hours[d]
            for d in DAY_KEYS
            if isinstance(available_hours.get(d), dict)
            and available_hours[d].get("start")
            and available_hours[d].get("end")
        }
    start = available_hours.get("start")
    end = available_hours.get("end")
    if not (start and end):
        return {}
    days = available_days or {}
    return {d: {"start": start, "end": end} for d in DAY_KEYS if days.get(d)}


class CRUDProfessional:
    async def list_professionals(self, session: AsyncSession):
        result = await session.execute(
            select(Professional).where(Professional.is_active.is_(True))
        )
        return result.scalars().all()

    async def get_by_id(self, session: AsyncSession, id: str) -> Optional[Professional]:
        result = await session.execute(select(Professional).where(Professional.id == id))
        return result.scalar_one_or_none()

    async def list_all(
        self, session: AsyncSession, limit: int = 10, offset: int = 0
    ) -> list:
        result = await session.execute(
            select(Professional)
            .order_by(Professional.fullname.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count(self, session: AsyncSession) -> int:
        result = await session.execute(select(func.count(Professional.id)))
        return result.scalar()

    async def create(self, session: AsyncSession, data: dict) -> Professional:
        professional = Professional(**data)
        session.add(professional)
        await session.commit()
        await session.refresh(professional)
        return professional

    async def update(self, session: AsyncSession, id: str, data: dict) -> Optional[Professional]:
        professional = await self.get_by_id(session=session, id=id)
        if not professional:
            return None
        for key, value in data.items():
            setattr(professional, key, value)
        await session.commit()
        await session.refresh(professional)
        return professional

    async def delete(self, session: AsyncSession, id: str) -> bool:
        professional = await self.get_by_id(session=session, id=id)
        if not professional:
            return False
        await session.delete(professional)
        await session.commit()
        return True


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
        user_id: str,
        professional_id: str
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
                    Appointment.professional_id == professional_id,
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
        user_id: str,
        professional_id: str
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
                    Appointment.professional_id == professional_id,
                    Appointment.appointment_date >= start_of_month,
                    Appointment.appointment_date <= end_of_month
                )
            )
            .limit(1)
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, session: AsyncSession, id: str) -> Optional[Appointment]:
        result = await session.execute(select(Appointment).where(Appointment.id == id))
        return result.scalar_one_or_none()
    
    async def update_status_to_confirm(self, session: AsyncSession, id: str, status: str) -> Optional[Appointment]:
        appointment = await self.get_by_id(session, id)
        if not appointment:
            return None
        appointment.status = status
        await session.commit()
        await session.refresh(appointment)
        return appointment
    
    async def get_all(
        self,
        session: AsyncSession,
        username: str = None,
        status: str = None,
        limit: int = 10,
        offset: int = 0
    ):
        query = (
            select(Appointment)
            .options(
                joinedload(Appointment.user),
                joinedload(Appointment.professional)
            )
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        )
        
        if username:
            query = query.join(Appointment.user).filter(
                User.fullname.ilike(f"%{username}%")
            )
        
        if status:
            query = query.filter(Appointment.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return result.scalars().all()
    
    async def count(
        self,
        session: AsyncSession,
        username: str = None,
        status: str = None
    ):
        query = select(func.count(Appointment.id))
        
        if username:
            query = query.join(Appointment.user).filter(
                User.fullname.ilike(f"%{username}%")
            )
        
        if status:
            query = query.filter(Appointment.status == status)
        
        result = await session.execute(query)
        return result.scalar()
    
    async def update_status(
        self,
        session: AsyncSession,
        id: str,
        status: str
    ):
        query = select(Appointment).filter(Appointment.id == id)
        result = await session.execute(query)
        appointment = result.scalar_one_or_none()

        if appointment:
            appointment.status = status
            await session.commit()
            await session.refresh(appointment)

        return appointment

    async def delete(self, session: AsyncSession, id: str) -> bool:
        appointment = await self.get_by_id(session=session, id=id)
        if not appointment:
            return False
        await session.delete(appointment)
        await session.commit()
        return True

crud_appointment = CRUDAppointment()
crud_professional = CRUDProfessional()