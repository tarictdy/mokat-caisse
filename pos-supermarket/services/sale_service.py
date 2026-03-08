from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models.sale import PaymentMethod, Sale
from models.sale_item import SaleItem
from models.user import User
from repositories.sale_repo import SaleRepository
from services.promotion_service import PromotionService


@dataclass
class CartLine:
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    discount: Decimal


class SaleService:
    def __init__(self, sale_repo: SaleRepository, promotion_service: PromotionService) -> None:
        self.sale_repo = sale_repo
        self.promotion_service = promotion_service

    def build_receipt_number(self) -> str:
        return datetime.utcnow().strftime("RCPT%Y%m%d%H%M%S%f")

    def finalize_sale(self, user: User, payment_method: PaymentMethod, lines: list[CartLine]) -> Sale:
        total = sum((line.total_price for line in lines), Decimal("0.00"))
        discount_total = sum((line.discount for line in lines), Decimal("0.00"))
        sale = Sale(
            receipt_number=self.build_receipt_number(),
            user_id=user.id,
            total_amount=total,
            tax_amount=Decimal("0.00"),
            discount_amount=discount_total,
            payment_method=payment_method,
        )

        for line in lines:
            sale.items.append(
                SaleItem(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount=line.discount,
                    total_price=line.total_price,
                )
            )

        return self.sale_repo.add(sale)
