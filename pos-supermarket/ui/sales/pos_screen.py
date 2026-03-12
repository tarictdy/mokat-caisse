from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from hardware.barcode_scanner import BarcodeScanner
from models.user import User
from services.payment_service import PaymentService
from services.printer_service import PrinterService
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
        self.printer_service = PrinterService()
        self.payment_service = PaymentService()
        self.barcode_scanner = BarcodeScanner()
        self.cart_lines: list[CartLine] = []
        self.held_sale_lines: list[CartLine] = []

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

        self.cash_btn = QPushButton("F1 Cash")
        self.cash_btn.clicked.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        self.mobile_btn = QPushButton("F2 Mobile")
        self.mobile_btn.clicked.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        self.remove_btn = QPushButton("F3 Annuler produit")
        self.remove_btn.clicked.connect(self._remove_last_product)
        self.hold_btn = QPushButton("F4 Vente en attente")
        self.hold_btn.clicked.connect(self._hold_current_sale)
        self.pay_button = QPushButton("Valider paiement")
        self.pay_button.setMinimumHeight(46)
        self.pay_button.clicked.connect(self._open_payment)

        pay_layout.addWidget(self.total_label, 1)
        pay_layout.addWidget(self.cash_btn)
        pay_layout.addWidget(self.mobile_btn)
        pay_layout.addWidget(self.remove_btn)
        pay_layout.addWidget(self.hold_btn)
        pay_layout.addWidget(self.pay_button)
        root.addWidget(payment_card)

        self.preview = ReceiptPreview()
        self._install_shortcuts()
        QTimer.singleShot(0, self._focus_scan_input)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._focus_scan_input()

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        QShortcut(QKeySequence("F3"), self).activated.connect(self._remove_last_product)
        QShortcut(QKeySequence("F4"), self).activated.connect(self._hold_current_sale)

    def _focus_scan_input(self) -> None:
        self.scan_input.setFocus()

    def _scan_product(self) -> None:
        barcode = self.barcode_scanner.normalize_code(self.scan_input.text())
        if not self.barcode_scanner.is_valid_scan(barcode):
            self._focus_scan_input()
            return

        product = self.sale_service.find_product_by_barcode(barcode)
        if not product:
            QApplication.beep()
            QMessageBox.warning(self, "Produit introuvable", f"Aucun produit pour le code {barcode}")
            self.scan_input.clear()
            self._focus_scan_input()
            return

        self.sale_service.add_product_to_cart(self.cart_lines, product)
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        QApplication.beep()
        self.scan_input.clear()
        self._focus_scan_input()

    def _remove_last_product(self) -> None:
        if not self.cart_lines:
            return
        self.cart_lines.pop()
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        self._focus_scan_input()

    def _hold_current_sale(self) -> None:
        if not self.cart_lines:
            return
        self.held_sale_lines = deepcopy(self.cart_lines)
        self.cart_lines = []
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        QMessageBox.information(self, "Vente en attente", "La vente en cours a été mise en attente.")
        self._focus_scan_input()

    def _refresh_total(self) -> Decimal:
        total = self.sale_service.compute_total(self.cart_lines)
        self.total_label.setText(f"TOTAL A PAYER : {int(total)} FCFA")
        return total

    def _open_payment(self, preferred_channel: str | None = None) -> None:
        total = self._refresh_total()
        if total <= 0:
            QMessageBox.information(self, "Panier vide", "Scannez au moins un produit avant de payer.")
            self._focus_scan_input()
            return

        dialog = PaymentDialog(total, self)
        if preferred_channel:
            dialog.set_preferred_channel(preferred_channel)

        if dialog.exec() != PaymentDialog.DialogCode.Accepted:
            self._focus_scan_input()
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
        self.printer_service.print_and_cut(
            receipt,
            open_drawer=self.payment_service.is_cash_payment(dialog.selected_channel),
        )
        self.preview.set_receipt(receipt)
        self.preview.show()

        self.cart_lines = []
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        self._focus_scan_input()
