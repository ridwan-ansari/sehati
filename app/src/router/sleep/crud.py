from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.sleep import Sleep


class CRUDSleep:

    async def create(
        self, 
        session: AsyncSession, 
        user_id: str, 
        sleep_time: datetime, 
        wake_up_time: datetime, 
        target_sleep_hours: int
    ):
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        sleep_date = sleep_time.date()
        wake_up_date = wake_up_time.date()
        
        if sleep_date not in [yesterday, today]:
            raise ValueError("Sleep time must be yesterday or today")
        
        if wake_up_date != today:
            raise ValueError("Wake up time must be today")
        
        if wake_up_time <= sleep_time:
            raise ValueError("Wake up time must be after sleep time")
        
        stmt = select(func.count(Sleep.id)).where(
            and_(
                Sleep.user_id == user_id,
                func.date(Sleep.created_at) == today
            )
        )
        result = await session.execute(stmt)
        count = result.scalar()
        
        if count > 0:
            raise ValueError("You have already submitted a sleep record today")
        
        sleep_duration_minutes = int((wake_up_time - sleep_time).total_seconds() / 60)

        record = Sleep(
            user_id=user_id,
            sleep_time=sleep_time,
            wake_up_time=wake_up_time,
            sleep_duration_minutes=sleep_duration_minutes,
            target_sleep_hours=target_sleep_hours
        )

        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def get_by_id(self, session: AsyncSession, sleep_id: str, user_id: str):
        stmt = select(Sleep).where(Sleep.id == sleep_id, Sleep.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self, 
        session: AsyncSession, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ):
        stmt = (
            select(Sleep)
            .where(Sleep.user_id == user_id)
            .order_by(Sleep.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_total_by_user(self, session: AsyncSession, user_id: str):
        stmt = select(func.count(Sleep.id)).where(Sleep.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar()

sleep_crud = CRUDSleep()