from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey, UniqueConstraint
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class ForumPost(Base, TimestampMixin):
    __tablename__ = "forum_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user = relationship("User")
    likes = relationship("ForumLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan")


class ForumLike(Base, TimestampMixin):
    __tablename__ = "forum_likes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    post = relationship("ForumPost", back_populates="likes")
    user = relationship("User")

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_user_like"),)


class ForumComment(Base, TimestampMixin):
    __tablename__ = "forum_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    post = relationship("ForumPost", back_populates="comments")
    user = relationship("User")
