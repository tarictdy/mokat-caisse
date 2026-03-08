from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from models.promotion import Promotion


class PromotionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def active_for_product(self, product_id: int, on_date: date) -> list[Promotion]:
        stmt = select(Promotion).where(
            and_(
                Promotion.product_id == product_id,
                Promotion.active.is_(True),
                Promotion.start_date <= on_date,
                Promotion.end_date >= on_date,
            )
        )
        return list(self.session.execute(stmt).scalars().all())
