from __future__ import annotations
from datetime import timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.models.user import User
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
        other_participant = (
            select(
                ChatParticipant.room_id,
                ChatParticipant.user_id
            )
            .where(
                ChatParticipant.user_id != user_id,
                ChatParticipant.deleted_at.is_(None)
            )
            .cte('other_participant')
        )
        
        latest_message = (
            select(
                ChatMessage.room_id,
                ChatMessage.message,
                ChatMessage.created_at,
                func.row_number().over(
                    partition_by=ChatMessage.room_id,
                    order_by=ChatMessage.created_at.desc()
                ).label('rn')
            )
            .where(ChatMessage.deleted_at.is_(None))
            .cte('latest_message')
        )
        
        stmt = (
            select(
                ChatRoom.id,
                ChatRoom.room_key,
                User.id.label('receiver_id'),
                User.fullname.label('receiver_name'),
                User.picture.label('receiver_picture'),
                latest_message.c.message.label('latest_message'),
                latest_message.c.created_at.label('latest_message_created_at')
            )
            .join(ChatParticipant, ChatParticipant.room_id == ChatRoom.id)
            .join(other_participant, other_participant.c.room_id == ChatRoom.id)
            .join(User, User.id == other_participant.c.user_id)
            .outerjoin(
                latest_message,
                and_(
                    latest_message.c.room_id == ChatRoom.id,
                    latest_message.c.rn == 1
                )
            )
            .where(
                ChatParticipant.user_id == user_id,
                ChatParticipant.deleted_at.is_(None)
            )
            .order_by(
                latest_message.c.created_at.desc().nullslast(),
                ChatRoom.updated_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(stmt)
        
        return [
            {
                "room_id": row.id,
                "room_key": row.room_key,
                "receiver_id": row.receiver_id,
                "receiver_name": row.receiver_name,
                "receiver_picture": row.receiver_picture,
                "latest_message": row.latest_message,
                "latest_message_created_at": row.latest_message_created_at + timedelta(hours=7)
            }
            for row in result.all()
        ]