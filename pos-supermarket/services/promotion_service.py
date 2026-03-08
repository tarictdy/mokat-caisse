from __future__ import annotations

from datetime import date
from decimal import Decimal

from models.product import Product
from models.promotion import Promotion, PromotionType
from repositories.promotion_repo import PromotionRepository


class PromotionService:
    def __init__(self, repo: PromotionRepository) -> None:
        self.repo = repo

    def get_active_promotions(self, product: Product, today: date | None = None) -> list[Promotion]:
        on_date = today or date.today()
        return self.repo.active_for_product(product.id, on_date)

    def apply_best_discount(self, product: Product, quantity: int) -> Decimal:
        promotions = self.get_active_promotions(product)
        subtotal = Decimal(product.sale_price) * quantity
        best_total = subtotal

        for promo in promotions:
            if promo.type == PromotionType.PERCENTAGE and promo.percentage_discount is not None:
                discounted = subtotal * (Decimal("1.00") - Decimal(promo.percentage_discount) / Decimal("100.00"))
            elif promo.type == PromotionType.FIXED and promo.fixed_discount is not None:
                discounted = max(Decimal("0.00"), subtotal - Decimal(promo.fixed_discount))
            elif (
                promo.type == PromotionType.BUY_X_GET_Y
                and promo.buy_quantity
                and promo.free_quantity
                and promo.buy_quantity > 0
            ):
                free_units = (quantity // (promo.buy_quantity + promo.free_quantity)) * promo.free_quantity
                discounted = Decimal(product.sale_price) * (quantity - free_units)
            else:
                discounted = subtotal

            if discounted < best_total:
                best_total = discounted

        return best_total
