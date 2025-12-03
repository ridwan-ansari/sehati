from __future__ import annotations
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.user import User
from app.src.models.point import (
    PointCategory,
    PointWallet,
    PointTransaction,
    CategoryCode,
    WalletKind,
    TxType,
)
import uuid


class CRUDPointCategory:
    async def get_all(self, session: AsyncSession):
        result = await session.execute(select(PointCategory))
        return result.scalars().all()

    async def get_by_code(self, session: AsyncSession, code: CategoryCode):
        result = await session.execute(
            select(PointCategory).where(PointCategory.code == code)
        )
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, **data) -> PointCategory:
        obj = PointCategory(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj


class CRUDPointWallet:

    async def get_all(self, session: AsyncSession):
        stmt = (
            select(PointWallet)
            .options(selectinload(PointWallet.user))
            .order_by(PointWallet.achievement_points.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, session: AsyncSession, user_id: str):
        result = await session.execute(
            select(PointWallet).where(PointWallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_wallet(self, session: AsyncSession, user_id: str):
        wallet = PointWallet(user_id=user_id)
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet

    async def update_balance(
        self,
        session: AsyncSession,
        user_id: str,
        wallet_type: WalletKind,
        amount: int,
        tx_type: TxType,
    ) -> PointWallet:
        wallet = await self.get_by_user(session, user_id)
        if not wallet:
            wallet = await self.create_wallet(session, user_id)

        if wallet_type == WalletKind.achievement:
            if tx_type == TxType.earn:
                wallet.achievement_points += amount 
            else:
                if wallet.achievement_points < amount:
                    raise ValueError("Transaction failed: Insufficient points.")
                wallet.achievement_points -= amount
            if wallet.achievement_points < 0:
                wallet.achievement_points = 0
        else:
            if tx_type == TxType.earn:
                wallet.credit_points += amount
            else:
                if wallet.credit_points < amount:
                    raise ValueError("Transaction failed: Insufficient credit points.")
                wallet.credit_points -= amount
            if wallet.credit_points < 0:
                wallet.credit_points = 0

        await session.commit()
        await session.refresh(wallet)
        return wallet


class CRUDPointTransaction:
    async def create(
        self,
        session: AsyncSession,
        user_id: str,
        wallet: WalletKind,
        tx_type: TxType,
        category_code: CategoryCode,
        delta: int,
        balance_after: int | None = None,
        note: str | None = None,
    ) -> PointTransaction:
        tx = PointTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            wallet=wallet,
            tx_type=tx_type,
            category_code=category_code,
            delta=delta,
            balance_after=balance_after,
            note=note,
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx

    async def get_history(
        self,
        session: AsyncSession,
        name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        stmt = (
            select(PointTransaction)
            .join(User, User.id == PointTransaction.user_id)
            .order_by(PointTransaction.created_at.desc())
            .options(selectinload(PointTransaction.user))
            .limit(limit)
            .offset(offset)
        )

        if name:
            stmt = stmt.where(User.fullname.ilike(f"%{name}%"))

        result = await session.execute(stmt)
        return result.scalars().all()
   
    async def exists_today(
        self,
        session: AsyncSession,
        user_id: str,
        category_code: CategoryCode,
    ):
        stmt = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .where(PointTransaction.category_code == category_code)
            .where(func.date(PointTransaction.created_at) == date.today())
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self, session: AsyncSession, name: str | None = None):
        stmt = (
            select(func.count(PointTransaction.id).label("total"))
            .join(User)
        )

        if name:
            stmt = stmt.where(User.fullname.ilike(f"%{name}%"))

        result = await session.execute(stmt)
        total = result.scalar_one()
        return total
    
crud_wallet = CRUDPointWallet()
crud_category = CRUDPointCategory()
crud_transaction = CRUDPointTransaction()