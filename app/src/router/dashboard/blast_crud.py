from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.models.blast_log import BlastLog


class CRUDBlastLog:
    async def create(self, session: AsyncSession, subject: str, body_html: str, recipients: List[str], cc: Optional[str] = None, created_by: Optional[str] = None) -> BlastLog:
        blast = BlastLog(
            subject=subject,
            body_html=body_html,
            recipients=recipients,
            cc=cc,
            created_by=created_by,
            status="pending"
        )
        session.add(blast)
        await session.commit()
        await session.refresh(blast)
        return blast

    async def update_status(self, session: AsyncSession, blast_id: str, status: str, sent_count: int, failed_count: int, error_log: dict) -> BlastLog:
        blast = await session.get(BlastLog, blast_id)
        if blast:
            blast.status = status
            blast.sent_count = sent_count
            blast.failed_count = failed_count
            blast.error_log = error_log
            session.add(blast)
            await session.commit()
            await session.refresh(blast)
        return blast

    async def get_by_id(self, session: AsyncSession, blast_id: str) -> Optional[BlastLog]:
        return await session.get(BlastLog, blast_id)

    async def get_all(self, session: AsyncSession, limit: int = 50, offset: int = 0) -> List[BlastLog]:
        stmt = select(BlastLog).where(BlastLog.deleted_at.is_(None)).order_by(desc(BlastLog.created_at)).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_failed(self, session: AsyncSession) -> List[BlastLog]:
        stmt = select(BlastLog).where((BlastLog.status == "partial_failed") | (BlastLog.status == "failed")).where(BlastLog.deleted_at.is_(None)).order_by(desc(BlastLog.created_at))
        result = await session.execute(stmt)
        return result.scalars().all()


crud_blast_log = CRUDBlastLog()
