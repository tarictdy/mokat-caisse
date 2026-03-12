from __future__ import annotations

from decimal import Decimal


class PaymentService:
    def calculate_change(self, amount_given: Decimal, total_amount: Decimal) -> Decimal:
        return amount_given - total_amount

    def is_payment_sufficient(self, amount_given: Decimal, total_amount: Decimal) -> bool:
        return amount_given >= total_amount
