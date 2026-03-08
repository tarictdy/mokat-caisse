from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.sale import Sale


class SaleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, sale: Sale) -> Sale:
        self.session.add(sale)
        self.session.flush()
        return sale

    def total_sales_for_day(self, day: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(func.date(Sale.created_at) == day.isoformat())
        value = self.session.execute(stmt).scalar_one()
        return Decimal(str(value))
