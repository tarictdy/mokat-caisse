from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class PromotionType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    BUY_X_GET_Y = "buy_x_get_y"


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    type: Mapped[PromotionType] = mapped_column(SAEnum(PromotionType), nullable=False)

    percentage_discount: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fixed_discount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    buy_quantity: Mapped[int | None] = mapped_column(nullable=True)
    free_quantity: Mapped[int | None] = mapped_column(nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="promotions")
