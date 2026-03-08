from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_barcode", "barcode"),
        Index("ix_products_internal_reference", "internal_reference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    internal_reference: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)

    purchase_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))

    stock_quantity: Mapped[int] = mapped_column(default=0)
    stock_min: Mapped[int] = mapped_column(default=0)
    stock_max: Mapped[int] = mapped_column(default=0)

    unit: Mapped[str] = mapped_column(String(20), default="piece")
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    promotion_eligible: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[ProductStatus] = mapped_column(SAEnum(ProductStatus), default=ProductStatus.ACTIVE)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    promotions = relationship("Promotion", back_populates="product")
