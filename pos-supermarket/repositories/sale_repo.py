from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.sale import Sale


class SaleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, sale_id: int) -> Sale | None:
        return self.session.execute(select(Sale).where(Sale.id == sale_id)).scalar_one_or_none()

    def add(self, sale: Sale) -> Sale:
        self.session.add(sale)
        self.session.flush()
        return sale

    def list_all(self) -> list[Sale]:
        return list(self.session.execute(select(Sale).order_by(Sale.created_at.desc())).scalars().all())

    def list_recent(self, limit: int = 20) -> list[Sale]:
        stmt = select(Sale).order_by(Sale.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_date_range(self, start_date: date, end_date: date) -> list[Sale]:
        stmt = select(Sale).where(
            func.date(Sale.created_at) >= start_date,
            func.date(Sale.created_at) <= end_date
        ).order_by(Sale.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def total_sales_for_day(self, day: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(func.date(Sale.created_at) == day.isoformat())
        value = self.session.execute(stmt).scalar_one()
        return Decimal(str(value))

    def total_sales_for_period(self, start_date: date, end_date: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
            func.date(Sale.created_at) >= start_date,
            func.date(Sale.created_at) <= end_date
        )
        value = self.session.execute(stmt).scalar_one()
        return Decimal(str(value))

    def count_sales_for_day(self, day: date) -> int:
        stmt = select(func.count(Sale.id)).where(func.date(Sale.created_at) == day.isoformat())
        return self.session.execute(stmt).scalar_one() or 0
