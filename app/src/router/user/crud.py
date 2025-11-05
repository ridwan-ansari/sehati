from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.src.models.user import User


class CRUDUser:
    async def create(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_user_by_id(self, session: AsyncSession, id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == id, User.verified.is_(True), User.role.in_("user"))
            .options(selectinload(User.user_nutritions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.verified.is_(True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(
        self,
        *filters,
        session: AsyncSession,
        keyword: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> List[User]:
        stmt = select(User).where(*filters, User.role.in_("user"))
        if keyword:
            stmt = stmt.where(User.fullname.ilike(f"%{keyword}%"))
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
