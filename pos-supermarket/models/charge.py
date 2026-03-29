from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ChargeCategory(str, Enum):
    SALAIRE = "salaire"
    LOYER = "loyer"
    ELECTRICITE = "electricite"
    EAU = "eau"
    INTERNET = "internet"
    TRANSPORT = "transport"
    MAINTENANCE = "maintenance"
    ACHAT_HORS_REVENTE = "achat_hors_revente"
    IMPOTS_TAXES = "impots_taxes"
    DIVERS = "divers"


class ChargeType(str, Enum):
    FIXE = "fixe"
    VARIABLE = "variable"
    SALARIALE = "salariale"
    DIVERSE = "diverse"


class Charge(Base):
    __tablename__ = "charges"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[ChargeCategory] = mapped_column(SAEnum(ChargeCategory), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    charge_date: Mapped[date] = mapped_column(Date, nullable=False)
    accounting_month: Mapped[str] = mapped_column(String(7), nullable=False)
    charge_type: Mapped[ChargeType] = mapped_column(SAEnum(ChargeType), nullable=False, default=ChargeType.DIVERSE)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
