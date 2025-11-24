from __future__ import annotations
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    youtube_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class VideoRewardClaim(Base, TimestampMixin):
    __tablename__ = "video_reward_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))

    __table_args__ = (UniqueConstraint("user_id", "video_id", name="uq_user_video_claim"),)