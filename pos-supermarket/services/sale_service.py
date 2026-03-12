from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.product import Product
from models.sale import PaymentMethod, Sale
from models.sale_item import SaleItem
from models.user import User
from repositories.product_repo import ProductRepository
from repositories.sale_repo import SaleRepository


@dataclass
class CartLine:
    product_id: int
    barcode: str
    product_name: str
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity


class SaleService:
    def __init__(self, sale_repo: SaleRepository, product_repo: ProductRepository) -> None:
        self.sale_repo = sale_repo
        self.product_repo = product_repo

    def build_receipt_number(self) -> str:
        return datetime.now().strftime("MK%Y%m%d%H%M%S%f")

    def find_product_by_barcode(self, barcode: str) -> Product | None:
        if not barcode.strip():
            return None
        return self.product_repo.get_by_barcode(barcode.strip())

    def add_product_to_cart(self, lines: list[CartLine], product: Product, quantity: int = 1) -> list[CartLine]:
        if quantity <= 0:
            return lines

        for line in lines:
            if line.product_id == product.id:
                line.quantity += quantity
                return lines

        lines.append(
            CartLine(
                product_id=product.id,
                barcode=product.barcode,
                product_name=product.name,
                quantity=quantity,
                unit_price=Decimal(str(product.sale_price)),
            )
        )
        return lines

    def compute_total(self, lines: list[CartLine]) -> Decimal:
        return sum((line.total_price for line in lines), Decimal("0.00"))

    def finalize_sale(
        self,
        user: User,
        payment_method: PaymentMethod,
        payment_channel: str,
        lines: list[CartLine],
        transaction_reference: str | None = None,
    ) -> Sale:
        total = self.compute_total(lines)
        sale = Sale(
            receipt_number=self.build_receipt_number(),
            user_id=user.id,
            total_amount=total,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            payment_method=payment_method,
            payment_channel=payment_channel,
            transaction_reference=transaction_reference or None,
        )

        for line in lines:
            sale.items.append(
                SaleItem(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount=Decimal("0.00"),
                    total_price=line.total_price,
                )
            )
            product = self.product_repo.get_by_id(line.product_id)
            if product:
                new_stock = max(0, product.stock_quantity - line.quantity)
                self.product_repo.update_stock(product.id, new_stock)

        return self.sale_repo.add(sale)
