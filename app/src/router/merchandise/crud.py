from __future__ import annotations
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy import select, func, case, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.merchandise import Merchandise, MerchandiseClaim

class CRUDMerchandise:

    async def create(self, session: AsyncSession, data: dict):
        obj = Merchandise(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def get_by_id(self, id: str, session: AsyncSession) -> Merchandise:
        stmt = select(Merchandise).where(Merchandise.id.__eq__(id), Merchandise.deleted_at.is_(None))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, session: AsyncSession, name: str = None, limit: int = 10, offset: int = 0):
        stmt = (
            select(Merchandise)
            .order_by(Merchandise.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if name:
            stmt = stmt.where(Merchandise.name.ilike(f"%{name}%"), Merchandise.description.ilike(f"%{name}%"))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(self, session: AsyncSession):
        result = await session.execute(select(func.count()).select_from(Merchandise))
        return result.scalar()

    async def update_stock(self, session: AsyncSession, id: str) -> Merchandise:
        merchandise = self.get_by_id(id=id, session=session)
        merchandise.stock -= 1
        await session.commit()
        await session.refresh(merchandise)
        return merchandise

    async def get_all_with_claim_status(
        self,
        session: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ):

        UserClaim = aliased(MerchandiseClaim)

        stmt = (
            select(
                Merchandise,
                UserClaim.status.label("claim_status"),
                case(
                    (UserClaim.id.is_not(None), True),
                    else_=False
                ).label("is_claim")
            )
            .outerjoin(
                UserClaim,
                (UserClaim.merchandise_id == Merchandise.id) &
                (UserClaim.user_id == user_id) &
                (UserClaim.deleted_at.is_(None))
            )
            .where(
                Merchandise.deleted_at.is_(None),
                Merchandise.active == True
            )
            .order_by(Merchandise.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.all()


class CRUDMerchandiseClaim:

    async def create(
        self,
        session: AsyncSession,
        user_id: str,
        merchandise_id: str,
        quantity: int = 1
    ) -> MerchandiseClaim:
        
        merchandise = await session.get(Merchandise, merchandise_id)
        
        if not merchandise:
            raise ValueError("Merchandise not found")
        
        if not merchandise.active:
            raise ValueError("Merchandise is not active")
        
        if merchandise.stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {merchandise.stock}")

        existing_claim = await session.execute(
            select(MerchandiseClaim)
            .where(
                MerchandiseClaim.user_id == user_id,
                MerchandiseClaim.merchandise_id == merchandise_id,
                MerchandiseClaim.deleted_at.is_(None)
            )
        )
        existing_claim = existing_claim.scalar_one_or_none()

        if existing_claim:
            raise ValueError("User has already claimed this merchandise")

        total_points = merchandise.price_points * quantity
        
        claim = MerchandiseClaim(
            user_id=user_id,
            merchandise_id=merchandise_id,
            quantity=quantity,
            total_points=total_points,
            status="pending"
        )
        
        merchandise.stock -= quantity
        
        session.add(claim)
        await session.commit()
        await session.refresh(claim)
        return claim
    
    async def get_by_id(self, id: str, session: AsyncSession) -> MerchandiseClaim:
        stmt = select(MerchandiseClaim).where(MerchandiseClaim.id.__eq__(id), MerchandiseClaim.deleted_at.is_(None)).options(selectinload(MerchandiseClaim.merchandise))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        session: AsyncSession,
        name: str | None = None,
        limit: int = 20,
        offset: int = 0
    ):
        stmt = (
            select(MerchandiseClaim)
            .order_by(MerchandiseClaim.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(MerchandiseClaim.user),
                selectinload(MerchandiseClaim.merchandise)
            )
        )

        if name:
            stmt = stmt.where(MerchandiseClaim.merchandise.has(Merchandise.name.ilike(f"%{name}%")))

        query = await session.execute(stmt)
        claims = query.scalars().all()

        return [
            {
                "fullname": c.user.fullname,
                "nickname": c.user.nickname,
                "merchandise_id": c.merchandise.id,
                "merchandise_name": c.merchandise.name,
                "merchandise_claim_status": c.status,
                "claim_id":c.id,
                "price_points":c.merchandise.price_points,
                "claimed_at": c.created_at,
            }
            for c in claims
        ]

    async def count(self, session: AsyncSession):
        result = await session.execute(select(func.count()).select_from(MerchandiseClaim))
        return result.scalar() or 0
    
    async def update_status(self, session: AsyncSession, claim_id: str, status: str):
        stmt = (
            update(MerchandiseClaim)
            .where(MerchandiseClaim.id == claim_id)
            .values(status=status)
        )
        await session.execute(stmt)
        await session.commit()


crud_merch = CRUDMerchandise()
crud_merch_claim = CRUDMerchandiseClaim()