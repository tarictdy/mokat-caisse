from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.charge import Charge


class ChargeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, charge: Charge) -> Charge:
        self.session.add(charge)
        self.session.flush()
        return charge

    def get_by_id(self, charge_id: int) -> Charge | None:
        return self.session.get(Charge, charge_id)

    def list_between_dates(self, start_date: date, end_date: date) -> list[Charge]:
        stmt = (
            select(Charge)
            .where(Charge.is_deleted.is_(False), Charge.charge_date >= start_date, Charge.charge_date <= end_date)
            .order_by(Charge.charge_date.desc(), Charge.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())
