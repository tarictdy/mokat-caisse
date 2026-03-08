from __future__ import annotations

from sqlalchemy.orm import Session

from models.sale import Sale


class SaleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, sale: Sale) -> Sale:
        self.session.add(sale)
        self.session.flush()
        return sale
