from __future__ import annotations

from decimal import Decimal

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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
        self.resize(980, 660)

        root = QVBoxLayout(self)
        title = QLabel("🛒 Interface Caisse")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        scan_card = QFrame()
        scan_card.setObjectName("Card")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.addWidget(QLabel("Scanner produit"))

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Champ scan code barre")
        self.scan_input.returnPressed.connect(self._scan_product)
        self.scan_input.setMinimumHeight(40)
        scan_layout.addWidget(self.scan_input)
        root.addWidget(scan_card)

        cart_card = QFrame()
        cart_card.setObjectName("Card")
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.addWidget(QLabel("Liste produits panier"))
        self.cart_widget = CartWidget()
        cart_layout.addWidget(self.cart_widget)
        root.addWidget(cart_card, 1)

        payment_card = QFrame()
        payment_card.setObjectName("Card")
        pay_layout = QHBoxLayout(payment_card)
        self.total_label = QLabel("TOTAL A PAYER : 0 FCFA")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.pay_button = QPushButton("Valider paiement")
        self.pay_button.setMinimumHeight(46)
        self.pay_button.clicked.connect(self._open_payment)
        pay_layout.addWidget(self.total_label, 1)
        pay_layout.addWidget(self.pay_button)
        root.addWidget(payment_card)

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
