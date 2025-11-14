from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.src.models.sleep import Sleep


class CRUDSleep:

    async def create(self, session: AsyncSession, user_id: str, start_time, wake_up_time, target_sleep_minutes: int):
        """Create a sleep record with auto-duration calculation."""

        # Konversi ke datetime dummy untuk hitung durasi
        today = datetime.today().date()
        dt_start = datetime.combine(today, start_time)
        dt_end = datetime.combine(today, wake_up_time)

        # Jika bangun lebih awal → berarti melewati tengah malam
        if dt_end <= dt_start:
            dt_end += timedelta(days=1)

        sleep_duration_minutes = int((dt_end - dt_start).total_seconds() / 60)

        record = Sleep(
            user_id=user_id,
            start_time=start_time,
            wake_up_time=wake_up_time,
            sleep_duration_minutes=sleep_duration_minutes,
            target_sleep_minutes=target_sleep_minutes
        )

        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def get_by_user(self, session: AsyncSession, user_id: str, limit: int = 20, offset: int = 0):
        stmt = (
            select(Sleep)
            .where(Sleep.user_id == user_id)
            .order_by(Sleep.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

sleep_crud = CRUDSleep()
