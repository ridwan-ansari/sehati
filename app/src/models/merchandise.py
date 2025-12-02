from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, Boolean, CheckConstraint, ForeignKey
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class Merchandise(Base, TimestampMixin):
    __tablename__ = "merchandise"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(512))
    price_points: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    claims = relationship("MerchandiseClaim", back_populates="merchandise", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("price_points >= 0", name="chk_merch_price_nonneg"),
        CheckConstraint("stock >= 0", name="chk_merch_stock_nonneg"),
    )


class MerchandiseClaim(Base, TimestampMixin):
    __tablename__ = "merchandise_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchandise_id: Mapped[str] = mapped_column(ForeignKey("merchandise.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    
    user = relationship("User", back_populates="merchandise_claims")
    merchandise = relationship("Merchandise", back_populates="claims")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_claim_qty_positive"),
    )