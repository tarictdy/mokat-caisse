from __future__ import annotations

from decimal import Decimal

from models.sale import PaymentMethod


class PaymentService:
    CASH_CHANNEL = "cash"
    WAVE_CHANNEL = "wave"
    ORANGE_MONEY_CHANNEL = "orange_money"
    MTN_MOMO_CHANNEL = "mtn_momo"
    CARD_CHANNEL = "card"

    @classmethod
    def payment_channels(cls) -> list[tuple[str, str, PaymentMethod]]:
        return [
            ("Espèces", cls.CASH_CHANNEL, PaymentMethod.CASH),
            ("Wave", cls.WAVE_CHANNEL, PaymentMethod.MOBILE),
            ("Orange Money", cls.ORANGE_MONEY_CHANNEL, PaymentMethod.MOBILE),
            ("MTN MoMo", cls.MTN_MOMO_CHANNEL, PaymentMethod.MOBILE),
            ("Carte bancaire", cls.CARD_CHANNEL, PaymentMethod.CARD),
        ]

    def resolve_payment_method(self, payment_channel: str) -> PaymentMethod:
        for _, channel, method in self.payment_channels():
            if channel == payment_channel:
                return method
        return PaymentMethod.CASH

    def is_cash_payment(self, payment_channel: str) -> bool:
        return payment_channel == self.CASH_CHANNEL

    def calculate_change(self, amount_given: Decimal, total_amount: Decimal) -> Decimal:
        return amount_given - total_amount

    def is_payment_sufficient(self, amount_given: Decimal, total_amount: Decimal, payment_channel: str) -> bool:
        if not self.is_cash_payment(payment_channel):
            return True
        return amount_given >= total_amount
