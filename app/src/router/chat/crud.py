from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
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
    
    async def get_user_room_by_key(
        self,
        session: AsyncSession,
        room_key: str,
        user_id: str
    ) -> ChatRoom | None:
        stmt = (
            select(ChatRoom)
            .join(ChatParticipant)
            .where(
                ChatParticipant.user_id == user_id,
                ChatParticipant.deleted_at.is_(None),
                ChatRoom.room_key == room_key,
                ChatRoom.deleted_at.is_(None)
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_rooms(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ):
        stmt = (
            select(ChatRoom)
            .options(
                selectinload(ChatRoom.participants).selectinload(ChatParticipant.user)
            )
            .join(ChatParticipant)
            .where(
                ChatParticipant.user_id == user_id,
                ChatParticipant.deleted_at.is_(None)
            )
            .order_by(ChatRoom.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        rooms = result.scalars().unique().all()

        room_list = []
        for room in rooms:
            receiver = next(
                (p.user for p in room.participants if p.user_id != user_id and p.deleted_at is None),
                None
            )
            if receiver:
                room_list.append({
                    "room_id": room.id,
                    "room_key": room.room_key,
                    "receiver_id": receiver.id,
                    "receiver_name": receiver.fullname,
                    "receiver_picture": receiver.picture
                })

        return room_list
