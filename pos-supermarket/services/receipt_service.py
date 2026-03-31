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

        lines += [
            "",
            "--------------------------------",
            f"Sous-total     {self._format_money(sale.total_amount + sale.discount_amount)}",
        ]
        if sale.discount_amount > 0:
            lines.append(f"Reduction      -{self._format_money(sale.discount_amount)}")
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

    def generate_receipt(
        self,
        sale: Sale,
        lines: list[CartLine],
        cashier_name: str,
        amount_received: Decimal,
        change: Decimal,
    ) -> str:
        """Alias simplifie pour build_receipt_text - compatibilite avec pos_screen"""
        from models.user import User
        # Creer un objet User temporaire pour le nom du caissier
        parts = cashier_name.split(" ", 1)
        temp_user = User(
            username=cashier_name,
            password_hash="",
            prenom=parts[0] if parts else cashier_name,
            nom=parts[1] if len(parts) > 1 else "",
        )
        return self.build_receipt_text(sale, temp_user, amount_received, change, lines)

    def print_receipt(self, receipt_text: str) -> None:
        # Hook for python-escpos integration.
        _ = receipt_text
