from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

from PyQt6.QtCore import QTimer, Qt
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

        self.setWindowTitle("MOKAT MARKET — Caisse")
        self.resize(1060, 720)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top header bar ────────────────────────────────────
        header = QWidget()
        header.setObjectName("TopBar")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(12)

        brand_lbl = QLabel("MOKAT MARKET")
        brand_lbl.setStyleSheet("color: #2563EB; font-size: 14px; font-weight: 800; letter-spacing: 2px;")
        title_lbl = QLabel("|  Caisse")
        title_lbl.setStyleSheet("color: #94A3B8; font-size: 14px;")
        header_layout.addWidget(brand_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        cashier_lbl = QLabel(f"{cashier.prenom} {cashier.nom}")
        cashier_lbl.setStyleSheet("color: #374151; font-weight: 600;")
        header_layout.addWidget(cashier_lbl)
        root.addWidget(header)

        # ── Main body ─────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #F8FAFC;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(16)

        # Left column: scan + cart
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        # Scan card
        scan_card = QFrame(); scan_card.setObjectName("Card")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(20, 16, 20, 16)
        scan_layout.setSpacing(10)

        scan_header = QHBoxLayout()
        scan_title = QLabel("Scanner un produit")
        scan_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        scan_hint = QLabel("F1 Cash   F2 Mobile   F3 Annuler   F4 Attente")
        scan_hint.setStyleSheet("font-size: 11px; color: #94A3B8;")
        scan_header.addWidget(scan_title)
        scan_header.addStretch()
        scan_header.addWidget(scan_hint)
        scan_layout.addLayout(scan_header)

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Placez le curseur ici et scannez le code-barres...")
        self.scan_input.returnPressed.connect(self._scan_product)
        self.scan_input.setMinimumHeight(42)
        self.scan_input.setStyleSheet(
            "border: 2px solid #2563EB; border-radius: 8px; padding: 8px 12px;"
            "font-size: 14px; font-weight: 600;"
        )
        scan_layout.addWidget(self.scan_input)
        left_col.addWidget(scan_card)

        # Cart card
        cart_card = QFrame(); cart_card.setObjectName("Card")
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(20, 16, 20, 16)
        cart_layout.setSpacing(10)
        cart_title = QLabel("Panier")
        cart_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        cart_layout.addWidget(cart_title)
        self.cart_widget = CartWidget()
        cart_layout.addWidget(self.cart_widget)
        left_col.addWidget(cart_card, 1)

        body_layout.addLayout(left_col, 1)

        # Right column: total + actions
        right_col = QVBoxLayout()
        right_col.setSpacing(14)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Total card
        total_card = QFrame(); total_card.setObjectName("Card")
        total_layout = QVBoxLayout(total_card)
        total_layout.setContentsMargins(20, 20, 20, 20)
        total_layout.setSpacing(6)

        total_title = QLabel("Total a payer")
        total_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;")
        total_layout.addWidget(total_title)

        self.total_label = QLabel("0 FCFA")
        self.total_label.setStyleSheet(
            "font-size: 36px; font-weight: 800; color: #0F172A; margin-top: 4px;"
        )
        total_layout.addWidget(self.total_label)
        right_col.addWidget(total_card)

        # Payment buttons
        btn_card = QFrame(); btn_card.setObjectName("Card")
        btn_card_layout = QVBoxLayout(btn_card)
        btn_card_layout.setContentsMargins(20, 16, 20, 16)
        btn_card_layout.setSpacing(10)

        btn_section_lbl = QLabel("Encaissement")
        btn_section_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;")
        btn_card_layout.addWidget(btn_section_lbl)

        self.pay_button = QPushButton("Valider le paiement")
        self.pay_button.setObjectName("SuccessButton")
        self.pay_button.setMinimumHeight(52)
        self.pay_button.setStyleSheet(
            "font-size: 15px; font-weight: 700; border-radius: 10px;"
            "background: #16A34A; color: #FFFFFF; margin-bottom: 4px;"
        )
        self.pay_button.clicked.connect(self._open_payment)
        btn_card_layout.addWidget(self.pay_button)

        # Quick pay row
        quick_row = QHBoxLayout(); quick_row.setSpacing(8)
        self.cash_btn = QPushButton("F1 Cash")
        self.cash_btn.clicked.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        self.mobile_btn = QPushButton("F2 Mobile")
        self.mobile_btn.setObjectName("SecondaryButton")
        self.mobile_btn.clicked.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        quick_row.addWidget(self.cash_btn)
        quick_row.addWidget(self.mobile_btn)
        btn_card_layout.addLayout(quick_row)

        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background: #E2E8F0;")
        btn_card_layout.addWidget(sep)

        # Other actions
        self.remove_btn = QPushButton("F3  Annuler dernier produit")
        self.remove_btn.setObjectName("DangerButton")
        self.remove_btn.setMinimumHeight(38)
        self.remove_btn.clicked.connect(self._remove_last_product)

        self.hold_btn = QPushButton("F4  Mettre en attente")
        self.hold_btn.setObjectName("SecondaryButton")
        self.hold_btn.setMinimumHeight(38)
        self.hold_btn.clicked.connect(self._hold_current_sale)

        btn_card_layout.addWidget(self.remove_btn)
        btn_card_layout.addWidget(self.hold_btn)
        right_col.addWidget(btn_card)
        right_col.addStretch()

        body_layout.addLayout(right_col)
        right_col_widget_width = 280
        # Fix right column width
        right_frame = QWidget()
        right_frame.setFixedWidth(300)
        right_frame.setLayout(right_col)
        body_layout.addWidget(right_frame)

        root.addWidget(body, 1)

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
        QMessageBox.information(self, "Vente en attente", "La vente en cours a ete mise en attente.")
        self._focus_scan_input()

    def _refresh_total(self) -> Decimal:
        total = self.sale_service.compute_total(self.cart_lines)
        self.total_label.setText(f"{int(total):,} FCFA")
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
