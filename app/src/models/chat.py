from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.now, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.now, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    room = relationship("ChatRoom", back_populates="participants")

    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_user"),)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    message: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.now, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    room = relationship("ChatRoom", back_populates="messages")
