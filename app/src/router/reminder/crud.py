
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.src.models.reminder import Reminder
from app.src.router.reminder.schema import ReminderBase, ReminderUpdate


class CRUDReminder:

    async def create(self, session: AsyncSession, data: ReminderBase, user_id: str):
        new_reminder = Reminder(**data.model_dump(), user_id=user_id)
        session.add(new_reminder)
        await session.commit()
        await session.refresh(new_reminder)
        return new_reminder

    async def get_by_id(self, session: AsyncSession, id: str, user_id: str):
        stmt = select(Reminder).where(Reminder.id == id, Reminder.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(self, session: AsyncSession, user_id: str, title: str = None, limit: int = None, offset: int = 0):
        stmt = select(Reminder).where(Reminder.user_id == user_id)
        if title:
            stmt = stmt.where(Reminder.title.ilike(f"%{title}%"))
        stmt = stmt.limit(limit=limit).offset(offset=offset)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(self, session: AsyncSession, id: str, data: ReminderUpdate, user_id: str):
        reminder = await self.get_by_id(session, id, user_id)
        if not reminder:
            return None

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)

        await session.commit()
        await session.refresh(reminder)
        return reminder

    async def delete(self, session: AsyncSession, id: str, user_id: str):
        stmt = delete(Reminder).where(Reminder.id == id, Reminder.user_id == user_id)
        await session.execute(stmt)
        await session.commit()
        return True


crud_reminder = CRUDReminder()
