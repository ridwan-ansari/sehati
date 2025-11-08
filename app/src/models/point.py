from __future__ import annotations
import uuid
from enum import Enum
from sqlalchemy import (
    String, Text, Integer, ForeignKey, CheckConstraint,
    Enum as SAEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.src.core.session import Base
from app.src.core.mixins import TimestampMixin


class CategoryCode(str, Enum):
    login = "login"
    watch_video = "watch_video"
    admin_bonus = "admin_bonus"
    food_diary = "food_diary"
    food_habit_answer = "food_habit_answer"
    exercise_answer = "exercise_answer"
    playing_game = "playing_game"
    merchandise_redeem = "merchandise_redeem"


class PointFlow(str, Enum):
    gain = "gain"
    spend = "spend"


class WalletKind(str, Enum):
    achievement = "achievement"
    credit = "credit"


class TxType(str, Enum):
    earn = "earn"
    spend = "spend"
    adjust = "adjust"


class PointCategory(Base, TimestampMixin):
    __tablename__ = "point_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[CategoryCode] = mapped_column(SAEnum(CategoryCode, name="cat_code_enum"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    default_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flow: Mapped[PointFlow] = mapped_column(SAEnum(PointFlow, name="point_flow_enum"), default=PointFlow.gain, nullable=False)
    daily_max: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (Index("ix_point_categories_code", "code"),)


class PointWallet(Base, TimestampMixin):
    __tablename__ = "point_wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credit_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user = relationship("User", back_populates="point_wallet")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_point_wallet_user"),
        CheckConstraint("achievement_points >= 0", name="chk_wallet_ap_nonneg"),
        CheckConstraint("credit_points >= 0", name="chk_wallet_cp_nonneg"),
    )


class PointTransaction(Base, TimestampMixin):
    __tablename__ = "point_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet: Mapped[WalletKind] = mapped_column(SAEnum(WalletKind, name="wallet_kind_enum"), nullable=False)
    tx_type: Mapped[TxType] = mapped_column(SAEnum(TxType, name="tx_type_enum"), nullable=False)
    category_code: Mapped[CategoryCode] = mapped_column(SAEnum(CategoryCode, name="tx_cat_code_enum"), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    user = relationship("User")

    __table_args__ = (Index("ix_point_tx_user_created", "user_id", "created_at"),)
