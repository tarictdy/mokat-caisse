from __future__ import annotations

from decimal import Decimal

from models.product import Product
from repositories.product_repo import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    def create_product(self, barcode: str, name: str, sale_price: Decimal, stock_quantity: int = 0) -> Product:
        existing = self.repo.get_by_barcode(barcode)
        if existing:
            raise ValueError("Barcode already exists")

        product = Product(barcode=barcode, name=name, sale_price=sale_price, stock_quantity=stock_quantity)
        return self.repo.add(product)

    def search_by_barcode(self, barcode: str) -> Product | None:
        return self.repo.get_by_barcode(barcode)

    def list_products(self) -> list[Product]:
        return self.repo.list_all()
