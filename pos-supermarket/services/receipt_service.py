from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from models.sale import Sale
from models.user import User
from services.sale_service import CartLine


class ReceiptService:
    store_name = "MOKATSHOP"
    store_location = "Songon"

    def _format_money(self, amount: Decimal) -> str:
        return f"{int(amount)} FCFA"

    def build_receipt_text(
        self, sale: Sale, cashier: User, amount_given: Decimal, change: Decimal, cart_lines: list[CartLine]
    ) -> str:
        now = datetime.now()
        lines = [
            "--------------------------------",
            f"      {self.store_name}",
            f"      {self.store_location}",
            "--------------------------------",
            f"Date : {now.strftime('%d/%m/%Y')}",
            f"Heure : {now.strftime('%H:%M:%S')}",
            f"Caissier : {cashier.prenom}",
            "",
            f"Reçu N° : {sale.receipt_number}",
            "--------------------------------",
            "Produit        Qté   Prix",
            "--------------------------------",
        ]

        for line in cart_lines:
            short_name = line.product_name[:12]
            lines.append(f"{short_name:<13}{line.quantity:<6}{int(line.total_price):>5}")

        subtotal = sum((line.total_price for line in cart_lines), Decimal("0.00"))
        lines += [
            "",
            "--------------------------------",
            f"SOUS-TOTAL     {self._format_money(subtotal)}",
        ]
        if sale.discount_amount and sale.discount_amount > 0:
            lines.append(f"REMISE         -{self._format_money(sale.discount_amount)}")
        lines += [
            f"TOTAL          {self._format_money(sale.total_amount)}",
            f"Montant donné  {self._format_money(amount_given)}",
            f"Monnaie        {self._format_money(change)}",
            f"Mode paiement  {sale.payment_channel}",
            "--------------------------------",
        ]
        if sale.transaction_reference:
            lines.append(f"Réf transaction {sale.transaction_reference}")
        lines += [
            "Merci pour votre achat",
            "--------------------------------",
        ]
        return "\n".join(lines)

    def print_receipt(self, receipt_text: str) -> None:
        # Hook for python-escpos integration.
        _ = receipt_text
