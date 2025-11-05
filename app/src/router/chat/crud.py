from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.src.models.chat import ChatRoom, ChatParticipant, ChatMessage

class CRUDChat:
    def _generate_room_key(self, sender_id: int, receiver_id: int) -> str:
        sorted_ids = sorted([sender_id, receiver_id])
        return f"room::{sorted_ids[0]}::{sorted_ids[1]}"

    async def get_or_create_room(self, session: AsyncSession, sender_id: int, receiver_id: int) -> ChatRoom:
        room_key = self._generate_room_key(sender_id, receiver_id)

        stmt = select(ChatRoom).where(ChatRoom.room_key == room_key, ChatRoom.deleted_at.__eq__(None)).limit(1)
        existing = await session.execute(stmt)
        room = existing.scalar_one_or_none()

        if room:
            return room

        room = ChatRoom(room_key=room_key)
        session.add(room)
        await session.flush()

        session.add_all([
            ChatParticipant(room_id=room.id, user_id=sender_id),
            ChatParticipant(room_id=room.id, user_id=receiver_id)
        ])

        await session.commit()
        await session.refresh(room)
        return room

    async def save_message(self, session: AsyncSession, room_id: int, sender_id: int, message: str):
        msg = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            message=message
        )
        session.add(msg)
        await session.commit()
        return msg

    async def get_messages(self, session: AsyncSession, room_id: int, limit: int = None, offset: int = None):
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_user_rooms(self, session: AsyncSession, user_id: int) -> ChatRoom:
        stmt = (
            select(ChatRoom)
            .join(ChatParticipant)
            .where(ChatParticipant.user_id == user_id, ChatParticipant.deleted_at.__eq__(None))
        )
        result = await session.execute(stmt)
        return result.scalars().all()
