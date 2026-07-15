from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.src.models.user import User
from app.src.models.merchandise import MerchandiseClaim
from app.src.models.games import GameClaim
from app.src.models.point import PointWallet


class CRUDUser:
    async def create(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_user_by_id(self, session: AsyncSession, id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == id, User.verified.is_(True), User.role.__eq__("user"))
            .options(selectinload(User.user_nutritions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_admin_by_id(self, session: AsyncSession, id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == id, User.verified.is_(True), User.role.__eq__("admin"))
            .options(selectinload(User.user_nutritions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.verified.is_(True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_nickname(self, session: AsyncSession, nickname: str) -> Optional[User]:
        stmt = select(User).where(User.nickname == nickname, User.verified.is_(True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_admin_user(self, session: AsyncSession):
        stmt = (
            select(User)
            .where(User.verified.is_(True), User.role.__eq__("admin"))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(
        self,
        *filters,
        session: AsyncSession,
        keyword: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        user_id: str = None,
    ) -> List[User]:
        stmt = select(User).where(*filters, User.role.__eq__("user")).order_by(User.created_at.desc())
        if keyword:
            stmt = stmt.where(User.fullname.ilike(f"%{keyword}%"))
        if user_id:
            stmt = stmt.where(User.id != user_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_active_users(self, session: AsyncSession) -> List[User]:
        stmt = (
            select(User)
            .where(User.role == "user", User.verified.is_(True), User.active.is_(True))
            .order_by(User.fullname.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_fcm_token(self, session: AsyncSession, user_id: str, token: str | None) -> None:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return
        user.fcm_token = token
        session.add(user)
        await session.commit()

    async def delete_user(self, session: AsyncSession, user_id: str) -> bool:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        await session.execute(sa_delete(MerchandiseClaim).where(MerchandiseClaim.user_id == user_id))
        await session.execute(sa_delete(GameClaim).where(GameClaim.user_id == user_id))
        await session.execute(sa_delete(PointWallet).where(PointWallet.user_id == user_id))
        await session.delete(user)
        await session.commit()
        return True


crud_user = CRUDUser()