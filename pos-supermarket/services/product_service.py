from __future__ import annotations

from datetime import date
from decimal import Decimal

from models.product import Product, ProductStatus
from repositories.product_repo import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    def create_product(
        self,
        barcode: str,
        name: str,
        sale_price: Decimal,
        stock_quantity: int = 0,
        internal_reference: str | None = None,
        purchase_price: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        stock_min: int = 0,
        stock_max: int = 0,
        unit: str = "piece",
        brand: str | None = None,
        description: str | None = None,
        expiration_date: date | None = None,
        category_id: int | None = None,
        supplier_id: int | None = None,
        image_path: str | None = None,
        promotion_eligible: bool = True,
    ) -> Product:
        existing = self.repo.get_by_barcode(barcode)
        if existing:
            raise ValueError("Barcode already exists")

        if internal_reference and self.repo.get_by_reference(internal_reference):
            raise ValueError("Internal reference already exists")

        if stock_max > 0 and stock_quantity > stock_max:
            raise ValueError("Initial stock cannot be greater than stock max")

        product = Product(
            barcode=barcode,
            internal_reference=internal_reference,
            name=name,
            brand=brand,
            description=description,
            category_id=category_id,
            supplier_id=supplier_id,
            purchase_price=purchase_price,
            sale_price=sale_price,
            tax_rate=tax_rate,
            stock_quantity=stock_quantity,
            stock_min=stock_min,
            stock_max=stock_max,
            unit=unit,
            expiration_date=expiration_date,
            image_path=image_path,
            promotion_eligible=promotion_eligible,
            status=ProductStatus.ACTIVE,
        )
        return self.repo.add(product)

    def search_by_barcode(self, barcode: str) -> Product | None:
        return self.repo.get_by_barcode(barcode)

    def list_products(self) -> list[Product]:
        return self.repo.list_all()
