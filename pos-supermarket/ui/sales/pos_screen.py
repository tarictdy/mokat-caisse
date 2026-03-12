from __future__ import annotations

from decimal import Decimal

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from models.user import User
from services.receipt_service import ReceiptService
from services.sale_service import CartLine, SaleService
from ui.sales.cart_widget import CartWidget
from ui.sales.payment_dialog import PaymentDialog
from ui.sales.receipt_preview import ReceiptPreview


class POSScreen(QWidget):
    def __init__(self, sale_service: SaleService, cashier: User) -> None:
        super().__init__()
        self.sale_service = sale_service
        self.cashier = cashier
        self.receipt_service = ReceiptService()
        self.cart_lines: list[CartLine] = []

        self.setWindowTitle("Caisse - MokatShop")

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Champ scan code barre")
        self.scan_input.returnPressed.connect(self._scan_product)

        self.cart_widget = CartWidget()
        self.total_label = QLabel("TOTAL A PAYER : 0 FCFA")
        self.pay_button = QPushButton("Valider paiement")
        self.pay_button.clicked.connect(self._open_payment)

        top_layout = QVBoxLayout(self)
        top_layout.addWidget(QLabel("Scan produit"))
        top_layout.addWidget(self.scan_input)
        top_layout.addWidget(QLabel("Liste produits panier"))
        top_layout.addWidget(self.cart_widget)
        top_layout.addWidget(self.total_label)

        payment_row = QHBoxLayout()
        payment_row.addWidget(QLabel("Paiement"))
        payment_row.addWidget(self.pay_button)
        top_layout.addLayout(payment_row)

        self.preview = ReceiptPreview()

    def _scan_product(self) -> None:
        barcode = self.scan_input.text().strip()
        product = self.sale_service.find_product_by_barcode(barcode)
        if not product:
            QMessageBox.warning(self, "Produit introuvable", f"Aucun produit pour le code {barcode}")
            return

        self.sale_service.add_product_to_cart(self.cart_lines, product)
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        self.scan_input.clear()

    def _refresh_total(self) -> Decimal:
        total = self.sale_service.compute_total(self.cart_lines)
        self.total_label.setText(f"TOTAL A PAYER : {int(total)} FCFA")
        return total

    def _open_payment(self) -> None:
        total = self._refresh_total()
        if total <= 0:
            QMessageBox.information(self, "Panier vide", "Scannez au moins un produit avant de payer.")
            return

        dialog = PaymentDialog(total, self)
        if dialog.exec() != PaymentDialog.DialogCode.Accepted:
            return

        sale = self.sale_service.finalize_sale(
            self.cashier,
            dialog.selected_method,
            dialog.selected_channel,
            self.cart_lines,
            dialog.transaction_reference,
        )
        receipt = self.receipt_service.build_receipt_text(
            sale, self.cashier, dialog.amount_given, dialog.change, self.cart_lines
        )
        self.receipt_service.print_receipt(receipt)
        self.preview.set_receipt(receipt)
        self.preview.show()

        self.cart_lines = []
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
