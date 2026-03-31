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
        discount_amount: Decimal = Decimal("0.00"),
    ) -> Sale:
        subtotal = self.compute_total(lines)
        applied_discount = max(Decimal("0.00"), min(discount_amount, subtotal))
        total = subtotal - applied_discount
        sale = Sale(
            receipt_number=self.build_receipt_number(),
            user_id=user.id,
            total_amount=total,
            tax_amount=Decimal("0.00"),
            discount_amount=applied_discount,
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

    def create_sale(
        self,
        lines: list[CartLine],
        cashier_id: int,
        discount_percent: Decimal = Decimal("0"),
        amount_received: Decimal = Decimal("0"),
        payment_channel: str = "cash",
    ) -> Sale:
        """Wrapper simplifie pour creer une vente depuis POSScreen."""
        from repositories.user_repo import UserRepository
        from core.database import SessionLocal
        
        with SessionLocal() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(cashier_id)
            if not user:
                raise ValueError(f"Caissier introuvable: {cashier_id}")
        
        payment_method = PaymentMethod.CASH
        if payment_channel in ("wave", "orange_money", "mtn_momo"):
            payment_method = PaymentMethod.MOBILE
        elif payment_channel == "card":
            payment_method = PaymentMethod.CARD
        
        subtotal = self.compute_total(lines)
        discount_amount = (subtotal * discount_percent / 100).quantize(Decimal("0.01")) if discount_percent > 0 else Decimal("0")
        
        return self.finalize_sale(
            user=user,
            payment_method=payment_method,
            payment_channel=payment_channel,
            lines=lines,
            discount_amount=discount_amount,
        )
