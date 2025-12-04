from __future__ import annotations
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Games(Base, TimestampMixin):
    __tablename__ = "games"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    namename: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(512))
    price_points: Mapped[int] = mapped_column(Integer, nullable=False)

    claims = relationship("GameClaim", back_populates="game", cascade="all, delete-orphan")


class GameClaim(Base, TimestampMixin):
    __tablename__ = "game_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    user = relationship("User", back_populates="game_claims")
    game = relationship("Games", back_populates="claims")
