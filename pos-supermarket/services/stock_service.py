from __future__ import annotations

from models.product import Product
from models.stock_movement import StockMovement, StockMovementType


class StockService:
    def adjust_stock(
        self,
        product: Product,
        movement_type: StockMovementType,
        quantity: int,
        reason: str | None = None,
        user_id: int | None = None,
    ) -> StockMovement:
        if movement_type == StockMovementType.ENTRY:
            product.stock_quantity += quantity
        else:
            product.stock_quantity -= quantity

        return StockMovement(
            product_id=product.id,
            type=movement_type,
            quantity=quantity,
            reason=reason,
            user_id=user_id,
        )
