from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.product import Product, ProductStatus


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, product_id: int) -> Product | None:
        return self.session.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()

    def get_by_barcode(self, barcode: str) -> Product | None:
        return self.session.execute(select(Product).where(Product.barcode == barcode)).scalar_one_or_none()

    def get_by_reference(self, reference: str) -> Product | None:
        return self.session.execute(
            select(Product).where(Product.internal_reference == reference)
        ).scalar_one_or_none()

    def list_all(self) -> list[Product]:
        return list(self.session.execute(select(Product).order_by(Product.name)).scalars().all())

    def count_all(self) -> int:
        return len(self.list_all())

    def count_low_stock(self) -> int:
        stmt = select(Product).where(Product.stock_quantity <= Product.stock_min)
        return len(list(self.session.execute(stmt).scalars().all()))

    def search_by_name_or_barcode(self, query: str, limit: int = 20) -> list[Product]:
        like_value = f"%{query.strip()}%"
        stmt = (
            select(Product)
            .where(
                or_(
                    Product.name.ilike(like_value),
                    Product.barcode.ilike(like_value),
                    Product.internal_reference.ilike(like_value),
                    Product.brand.ilike(like_value),
                )
            )
            .order_by(Product.name)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def latest_created(self, limit: int = 10) -> list[Product]:
        stmt = select(Product).order_by(Product.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product

    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        self.session.delete(product)
        self.session.flush()
        return True

    def restock(self, product_id: int, quantity: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.stock_quantity += quantity
        self.session.flush()
        return True

    def update_stock(self, product_id: int, quantity: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.stock_quantity = quantity
        self.session.flush()
        return True

    def set_status(self, product_id: int, status: ProductStatus) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        product.status = status
        self.session.flush()
        return True
