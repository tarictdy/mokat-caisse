from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
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
    """Interface de caisse moderne - Mode clair, touch-friendly"""

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

        self.setWindowTitle("MOKAT MARKET - Caisse")
        self.resize(1400, 900)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Inter', sans-serif;
                background: #F8FAFC;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════
        # HEADER - Light mode
        # ══════════════════════════════════════════════════════
        header = QWidget()
        header.setFixedHeight(72)
        header.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(20)

        # Logo
        logo = QLabel("M")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            background: #2563EB;
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 800;
            border-radius: 12px;
        """)
        header_layout.addWidget(logo)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(2)
        brand_name = QLabel("MOKAT MARKET")
        brand_name.setStyleSheet("color: #0F172A; font-size: 16px; font-weight: 700; letter-spacing: 1px;")
        brand_sub = QLabel("Point de Vente")
        brand_sub.setStyleSheet("color: #64748B; font-size: 12px;")
        brand_col.addWidget(brand_name)
        brand_col.addWidget(brand_sub)
        header_layout.addLayout(brand_col)
        header_layout.addStretch()

        # Session badge
        session_lbl = QLabel("SESSION OUVERTE")
        session_lbl.setStyleSheet("""
            color: #059669;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: #D1FAE5;
            border-radius: 12px;
            padding: 8px 16px;
        """)
        header_layout.addWidget(session_lbl)

        # Cashier info
        initials = ""
        if cashier.prenom:
            initials += cashier.prenom[0].upper()
        if cashier.nom:
            initials += cashier.nom[0].upper()

        cashier_avatar = QLabel(initials or "?")
        cashier_avatar.setFixedSize(40, 40)
        cashier_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cashier_avatar.setStyleSheet("""
            background: #3B82F6;
            color: #FFFFFF;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
        """)
        cashier_name = QLabel(f"{cashier.prenom} {cashier.nom}")
        cashier_name.setStyleSheet("color: #334155; font-size: 14px; font-weight: 600;")
        header_layout.addWidget(cashier_avatar)
        header_layout.addWidget(cashier_name)

        root.addWidget(header)

        # ══════════════════════════════════════════════════════
        # BODY - 3 colonnes
        # ══════════════════════════════════════════════════════
        body = QWidget()
        body.setStyleSheet("background: #F1F5F9;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(24)

        # ─────────────────────────────────────────────────────
        # LEFT - Scanner + Quick Actions (240px)
        # ─────────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(280)
        left.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # Scanner card
        scan_card = QFrame()
        scan_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 2px solid #2563EB;
                border-radius: 16px;
            }
        """)
        scan_inner = QVBoxLayout(scan_card)
        scan_inner.setContentsMargins(20, 20, 20, 20)
        scan_inner.setSpacing(14)

        scan_badge = QLabel("SCANNER")
        scan_badge.setStyleSheet("""
            color: #2563EB;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            background: #EFF6FF;
            border-radius: 8px;
            padding: 6px 12px;
        """)
        scan_inner.addWidget(scan_badge)

        scan_title = QLabel("Saisir ou scanner\nun produit")
        scan_title.setStyleSheet("color: #0F172A; font-size: 15px; font-weight: 600; line-height: 1.3;")
        scan_inner.addWidget(scan_title)

        self.scan_input = QLineEdit()
        self.scan_input.setObjectName("ScanInput")
        self.scan_input.setPlaceholderText("Code-barres...")
        self.scan_input.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
                font-size: 16px;
                font-weight: 600;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
                background: #FFFFFF;
            }
        """)
        self.scan_input.returnPressed.connect(self._scan_product)
        scan_inner.addWidget(self.scan_input)

        left_layout.addWidget(scan_card)

        # Quick payment buttons - Large touch targets
        quick_title = QLabel("PAIEMENT RAPIDE")
        quick_title.setStyleSheet("""
            color: #64748B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 8px 0;
        """)
        left_layout.addWidget(quick_title)

        self.cash_btn = QPushButton("F1\nEspeces")
        self.cash_btn.setMinimumHeight(80)
        self.cash_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #0F172A;
                border: 2px solid #E2E8F0;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #F8FAFC;
                border-color: #CBD5E1;
            }
            QPushButton:pressed {
                background: #F1F5F9;
            }
        """)
        self.cash_btn.clicked.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        left_layout.addWidget(self.cash_btn)

        self.mobile_btn = QPushButton("F2\nMobile Money")
        self.mobile_btn.setMinimumHeight(80)
        self.mobile_btn.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #1D4ED8;
                border: 2px solid #BFDBFE;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #DBEAFE;
            }
            QPushButton:pressed {
                background: #BFDBFE;
            }
        """)
        self.mobile_btn.clicked.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        left_layout.addWidget(self.mobile_btn)

        # Actions title
        actions_title = QLabel("ACTIONS")
        actions_title.setStyleSheet("""
            color: #64748B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 16px 0 8px 0;
        """)
        left_layout.addWidget(actions_title)

        self.remove_btn = QPushButton("F3  Annuler article")
        self.remove_btn.setMinimumHeight(56)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #FEF2F2;
                color: #DC2626;
                border: 1.5px solid #FECACA;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #FEE2E2; }
        """)
        self.remove_btn.clicked.connect(self._remove_last_product)
        left_layout.addWidget(self.remove_btn)

        self.hold_btn = QPushButton("F4  Mettre en attente")
        self.hold_btn.setMinimumHeight(56)
        self.hold_btn.setStyleSheet("""
            QPushButton {
                background: #FFFBEB;
                color: #D97706;
                border: 1.5px solid #FDE68A;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #FEF3C7; }
        """)
        self.hold_btn.clicked.connect(self._hold_current_sale)
        left_layout.addWidget(self.hold_btn)

        self.clear_btn = QPushButton("Vider le panier")
        self.clear_btn.setMinimumHeight(56)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #64748B;
                border: 1.5px solid #E2E8F0;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #F8FAFC; }
        """)
        self.clear_btn.clicked.connect(self._clear_cart)
        left_layout.addWidget(self.clear_btn)

        left_layout.addStretch()

        # Keyboard hints
        hints = QLabel("F1 Especes  |  F2 Mobile  |  F3 Annuler  |  F4 Attente")
        hints.setStyleSheet("color: #94A3B8; font-size: 10px; padding: 8px 0;")
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(hints)

        body_layout.addWidget(left)

        # ─────────────────────────────────────────────────────
        # CENTER - Panier (flex)
        # ─────────────────────────────────────────────────────
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        cart_card = QFrame()
        cart_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 20px;
            }
        """)
        cart_inner = QVBoxLayout(cart_card)
        cart_inner.setContentsMargins(0, 0, 0, 0)
        cart_inner.setSpacing(0)

        # Cart header
        cart_header = QWidget()
        cart_header.setStyleSheet("background: #FAFBFC; border-top-left-radius: 20px; border-top-right-radius: 20px;")
        cart_header_layout = QHBoxLayout(cart_header)
        cart_header_layout.setContentsMargins(24, 18, 24, 18)

        cart_title = QLabel("Panier")
        cart_title.setStyleSheet("color: #0F172A; font-size: 18px; font-weight: 700;")
        cart_header_layout.addWidget(cart_title)
        cart_header_layout.addStretch()

        self.cart_count = QLabel("0 article")
        self.cart_count.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            font-weight: 600;
            background: #F1F5F9;
            border-radius: 10px;
            padding: 6px 14px;
        """)
        cart_header_layout.addWidget(self.cart_count)

        cart_inner.addWidget(cart_header)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0;")
        cart_inner.addWidget(sep)

        # Cart scroll area
        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cart_scroll.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: none;
            }
            QScrollBar:vertical {
                background: #F8FAFC;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 5px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.cart_widget = CartWidget()
        cart_scroll.setWidget(self.cart_widget)
        cart_inner.addWidget(cart_scroll, 1)

        center_layout.addWidget(cart_card)
        body_layout.addWidget(center, 1)

        # ─────────────────────────────────────────────────────
        # RIGHT - Total + Pay (360px)
        # ─────────────────────────────────────────────────────
        right = QWidget()
        right.setFixedWidth(380)
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)

        # Total card - Light blue accent
        total_card = QFrame()
        total_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EFF6FF, stop:1 #DBEAFE);
                border: 2px solid #BFDBFE;
                border-radius: 20px;
            }
        """)
        total_inner = QVBoxLayout(total_card)
        total_inner.setContentsMargins(28, 28, 28, 28)
        total_inner.setSpacing(8)

        total_title = QLabel("TOTAL A PAYER")
        total_title.setStyleSheet("""
            color: #1E40AF;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        total_inner.addWidget(total_title)

        self.total_label = QLabel("0 FCFA")
        self.total_label.setStyleSheet("""
            color: #1E3A8A;
            font-size: 44px;
            font-weight: 800;
            letter-spacing: -1px;
        """)
        total_inner.addWidget(self.total_label)

        self.tax_info = QLabel("TVA incluse")
        self.tax_info.setStyleSheet("color: #3B82F6; font-size: 12px; font-weight: 500;")
        total_inner.addWidget(self.tax_info)

        right_layout.addWidget(total_card)

        # Main pay button - Large touch target
        self.pay_button = QPushButton("Valider le paiement")
        self.pay_button.setMinimumHeight(72)
        self.pay_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10B981);
                color: #FFFFFF;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #047857, stop:1 #059669);
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        self.pay_button.clicked.connect(self._open_payment)
        right_layout.addWidget(self.pay_button)

        # Order summary card
        summary_card = QFrame()
        summary_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        summary_inner = QVBoxLayout(summary_card)
        summary_inner.setContentsMargins(24, 20, 24, 20)
        summary_inner.setSpacing(14)

        summary_title = QLabel("RESUME")
        summary_title.setStyleSheet("""
            color: #64748B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        summary_inner.addWidget(summary_title)

        # Sous-total row
        row1 = QHBoxLayout()
        row1_lbl = QLabel("Sous-total")
        row1_lbl.setStyleSheet("color: #64748B; font-size: 14px;")
        self.subtotal_lbl = QLabel("0 FCFA")
        self.subtotal_lbl.setStyleSheet("color: #334155; font-size: 14px; font-weight: 600;")
        row1.addWidget(row1_lbl)
        row1.addStretch()
        row1.addWidget(self.subtotal_lbl)
        summary_inner.addLayout(row1)

        # TVA row
        row2 = QHBoxLayout()
        row2_lbl = QLabel("TVA")
        row2_lbl.setStyleSheet("color: #64748B; font-size: 14px;")
        self.tax_lbl = QLabel("0 FCFA")
        self.tax_lbl.setStyleSheet("color: #334155; font-size: 14px; font-weight: 600;")
        row2.addWidget(row2_lbl)
        row2.addStretch()
        row2.addWidget(self.tax_lbl)
        summary_inner.addLayout(row2)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #E2E8F0;")
        summary_inner.addWidget(div)

        # Total row
        row3 = QHBoxLayout()
        row3_lbl = QLabel("Total")
        row3_lbl.setStyleSheet("color: #0F172A; font-size: 16px; font-weight: 700;")
        self.final_total_lbl = QLabel("0 FCFA")
        self.final_total_lbl.setStyleSheet("color: #059669; font-size: 18px; font-weight: 800;")
        row3.addWidget(row3_lbl)
        row3.addStretch()
        row3.addWidget(self.final_total_lbl)
        summary_inner.addLayout(row3)

        right_layout.addWidget(summary_card)
        right_layout.addStretch()

        body_layout.addWidget(right)
        root.addWidget(body, 1)

        self.preview = ReceiptPreview()
        self._install_shortcuts()
        QTimer.singleShot(0, self._focus_scan_input)

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._focus_scan_input()

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F1"), self).activated.connect(
            lambda: self._open_payment(PaymentService.CASH_CHANNEL)
        )
        QShortcut(QKeySequence("F2"), self).activated.connect(
            lambda: self._open_payment(PaymentService.WAVE_CHANNEL)
        )
        QShortcut(QKeySequence("F3"), self).activated.connect(self._remove_last_product)
        QShortcut(QKeySequence("F4"), self).activated.connect(self._hold_current_sale)

    def _focus_scan_input(self) -> None:
        self.scan_input.setFocus()

    # ──────────────────────────────────────────────────────────
    # Business logic handlers
    # ──────────────────────────────────────────────────────────

    def _scan_product(self) -> None:
        barcode = self.barcode_scanner.normalize_code(self.scan_input.text())
        if not self.barcode_scanner.is_valid_scan(barcode):
            self._focus_scan_input()
            return

        product = self.sale_service.find_product_by_barcode(barcode)
        if not product:
            QApplication.beep()
            QMessageBox.warning(
                self, "Produit introuvable",
                f"Aucun produit pour le code : {barcode}"
            )
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

    def _clear_cart(self) -> None:
        if not self.cart_lines:
            return
        if (
            QMessageBox.question(self, "Confirmation", "Voulez-vous vider le panier ?")
            == QMessageBox.StandardButton.Yes
        ):
            self.cart_lines = []
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
        QMessageBox.information(
            self, "Vente en attente",
            "La vente en cours a ete mise en attente."
        )
        self._focus_scan_input()

    def _refresh_total(self) -> Decimal:
        total = self.sale_service.compute_total(self.cart_lines)
        formatted = f"{int(total):,}".replace(",", " ")
        self.total_label.setText(f"{formatted} FCFA")
        self.subtotal_lbl.setText(f"{formatted} FCFA")
        self.final_total_lbl.setText(f"{formatted} FCFA")
        self.tax_lbl.setText("Incluse")
        count = len(self.cart_lines)
        self.cart_count.setText(f"{count} article{'s' if count != 1 else ''}")
        return total

    def _open_payment(self, preferred_channel: str | None = None) -> None:
        total = self._refresh_total()
        if total <= 0:
            QMessageBox.information(
                self, "Panier vide",
                "Scannez au moins un produit avant de payer."
            )
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
