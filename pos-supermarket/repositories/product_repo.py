from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_barcode(self, barcode: str) -> Product | None:
        return self.session.execute(select(Product).where(Product.barcode == barcode)).scalar_one_or_none()

    def list_all(self) -> list[Product]:
        return list(self.session.execute(select(Product).order_by(Product.name)).scalars().all())

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product
