from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

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
    QDialog,
    QFormLayout,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from hardware.barcode_scanner import BarcodeScanner
from models.user import User
from models.user import UserRole
from repositories.user_repo import UserRepository
from services.payment_service import PaymentService
from services.printer_service import PrinterService
from services.receipt_service import ReceiptService
from services.sale_service import CartLine, SaleService
from services.user_service import UserService
from ui.sales.cart_widget import CartWidget
from ui.sales.payment_dialog import PaymentDialog
from ui.sales.receipt_preview import ReceiptPreview


@dataclass
class PendingSale:
    ticket_id: int
    created_at: datetime
    lines: list[CartLine]
    discount_percent: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        subtotal = sum((line.total_price for line in self.lines), Decimal("0.00"))
        if self.discount_percent <= 0:
            return subtotal
        discount_amount = (subtotal * self.discount_percent / Decimal("100")).quantize(Decimal("0.01"))
        return max(Decimal("0.00"), subtotal - discount_amount)

    @property
    def item_count(self) -> int:
        return sum(line.quantity for line in self.lines)


class POSScreen(QWidget):
    """Interface de caisse - Style Vercel, touch-friendly"""

    def __init__(self, sale_service: SaleService, cashier: User) -> None:
        super().__init__()
        self.sale_service = sale_service
        self.cashier = cashier
        self.receipt_service = ReceiptService()
        self.printer_service = PrinterService()
        self.payment_service = PaymentService()
        self.barcode_scanner = BarcodeScanner()
        self.cart_lines: list[CartLine] = []
        self.pending_sales: list[PendingSale] = []
        self.pending_sale_counter = 1
        self.discount_percent = Decimal("0")

        self.setWindowTitle("MOKAT MARKET - Caisse")
        self.resize(1400, 900)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background: #FAFAFA;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════
        # HEADER - Vercel Style
        # ══════════════════════════════════════════════════════
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-bottom: 1px solid #EAEAEA;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(16)

        # Logo
        logo = QLabel("M")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            background: #000000;
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 700;
            border-radius: 8px;
        """)
        header_layout.addWidget(logo)

        brand_name = QLabel("MOKAT MARKET")
        brand_name.setStyleSheet("color: #000000; font-size: 15px; font-weight: 600; letter-spacing: 0.5px;")
        header_layout.addWidget(brand_name)

        sep = QLabel("|")
        sep.setStyleSheet("color: #D4D4D4; font-size: 20px; font-weight: 300;")
        header_layout.addWidget(sep)

        pos_label = QLabel("Point de Vente")
        pos_label.setStyleSheet("color: #666666; font-size: 14px;")
        header_layout.addWidget(pos_label)

        header_layout.addStretch()

        # Session badge
        session_badge = QLabel("SESSION ACTIVE")
        session_badge.setStyleSheet("""
            color: #0A8754;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: #D3F9E8;
            border-radius: 4px;
            padding: 6px 12px;
        """)
        header_layout.addWidget(session_badge)

        # Cashier
        initials = ""
        if cashier.prenom:
            initials += cashier.prenom[0].upper()
        if cashier.nom:
            initials += cashier.nom[0].upper()

        cashier_avatar = QLabel(initials or "?")
        cashier_avatar.setFixedSize(32, 32)
        cashier_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cashier_avatar.setStyleSheet("""
            background: #000000;
            color: #FFFFFF;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
        """)
        cashier_name = QLabel(f"{cashier.prenom} {cashier.nom}")
        cashier_name.setStyleSheet("color: #000000; font-size: 14px; font-weight: 500;")
        header_layout.addWidget(cashier_avatar)
        header_layout.addWidget(cashier_name)

        root.addWidget(header)

        # ══════════════════════════════════════════════════════
        # BODY - 3 colonnes
        # ══════════════════════════════════════════════════════
        body = QWidget()
        body.setStyleSheet("background: #FAFAFA;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(20)

        # ─────────────────────────────────────────────────────
        # LEFT - Scanner + Actions (260px)
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
                border: 1px solid #EAEAEA;
                border-radius: 12px;
            }
        """)
        scan_inner = QVBoxLayout(scan_card)
        scan_inner.setContentsMargins(20, 20, 20, 20)
        scan_inner.setSpacing(16)

        scan_title = QLabel("Scanner un produit")
        scan_title.setStyleSheet("color: #000000; font-size: 14px; font-weight: 600;")
        scan_inner.addWidget(scan_title)

        self.scan_input = QLineEdit()
        self.scan_input.setObjectName("ScanInput")
        self.scan_input.setPlaceholderText("Code-barres...")
        self.scan_input.setStyleSheet("""
            QLineEdit {
                background: #FAFAFA;
                border: 2px solid #EAEAEA;
                border-radius: 8px;
                padding: 14px 16px;
                font-size: 16px;
                font-weight: 500;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #000000;
                background: #FFFFFF;
            }
        """)
        self.scan_input.returnPressed.connect(self._scan_product)
        scan_inner.addWidget(self.scan_input)

        left_layout.addWidget(scan_card)

        # Payment section
        pay_title = QLabel("PAIEMENT")
        pay_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; letter-spacing: 1px; padding: 8px 0;")
        left_layout.addWidget(pay_title)

        self.cash_btn = QPushButton("F1  Especes")
        self.cash_btn.setMinimumHeight(56)
        self.cash_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #000000;
                border: 1px solid #EAEAEA;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #F5F5F5; }
            QPushButton:pressed { background: #EAEAEA; }
        """)
        self.cash_btn.clicked.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        left_layout.addWidget(self.cash_btn)

        self.mobile_btn = QPushButton("F2  Mobile Money")
        self.mobile_btn.setMinimumHeight(56)
        self.mobile_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #000000;
                border: 1px solid #EAEAEA;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #F5F5F5; }
            QPushButton:pressed { background: #EAEAEA; }
        """)
        self.mobile_btn.clicked.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        left_layout.addWidget(self.mobile_btn)

        # Actions section
        act_title = QLabel("ACTIONS")
        act_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; letter-spacing: 1px; padding: 16px 0 8px 0;")
        left_layout.addWidget(act_title)

        self.remove_btn = QPushButton("F3  Annuler article")
        self.remove_btn.setMinimumHeight(48)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #EE0000;
                border: 1px solid #FFE5E5;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #FFF5F5; }
        """)
        self.remove_btn.clicked.connect(self._remove_last_product)
        left_layout.addWidget(self.remove_btn)

        self.hold_btn = QPushButton("F4  Mettre en attente")
        self.hold_btn.setMinimumHeight(48)
        self.hold_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #9A6700;
                border: 1px solid #FFF4D6;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #FFFBEB; }
        """)
        self.hold_btn.clicked.connect(self._hold_current_sale)
        left_layout.addWidget(self.hold_btn)

        self.clear_btn = QPushButton("Vider le panier")
        self.clear_btn.setMinimumHeight(48)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #666666;
                border: 1px solid #EAEAEA;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background: #F5F5F5; }
        """)
        self.clear_btn.clicked.connect(self._clear_cart)
        left_layout.addWidget(self.clear_btn)

        left_layout.addStretch()

        # Shortcuts hint
        hints = QLabel("F1 Especes | F2 Mobile | F3 Annuler | F4 Attente")
        hints.setStyleSheet("color: #A3A3A3; font-size: 10px; padding: 8px 0;")
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
                border: 1px solid #EAEAEA;
                border-radius: 12px;
            }
        """)
        cart_inner = QVBoxLayout(cart_card)
        cart_inner.setContentsMargins(0, 0, 0, 0)
        cart_inner.setSpacing(0)

        # Cart header
        cart_header = QWidget()
        cart_header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #EAEAEA; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        cart_header_layout = QHBoxLayout(cart_header)
        cart_header_layout.setContentsMargins(20, 16, 20, 16)

        cart_title = QLabel("Panier")
        cart_title.setStyleSheet("color: #000000; font-size: 16px; font-weight: 600;")
        cart_header_layout.addWidget(cart_title)
        cart_header_layout.addStretch()

        self.cart_count = QLabel("0 article")
        self.cart_count.setStyleSheet("""
            color: #666666;
            font-size: 13px;
            font-weight: 500;
            background: #F5F5F5;
            border-radius: 4px;
            padding: 4px 10px;
        """)
        cart_header_layout.addWidget(self.cart_count)

        cart_inner.addWidget(cart_header)

        # Cart scroll area
        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cart_scroll.setStyleSheet("""
            QScrollArea { background: #FFFFFF; border: none; }
            QScrollBar:vertical { background: transparent; width: 8px; }
            QScrollBar::handle:vertical { background: #D4D4D4; border-radius: 4px; min-height: 40px; }
            QScrollBar::handle:vertical:hover { background: #A3A3A3; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
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
        right.setFixedWidth(360)
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Total card - Clean white
        total_card = QFrame()
        total_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EAEAEA;
                border-radius: 12px;
            }
        """)
        total_inner = QVBoxLayout(total_card)
        total_inner.setContentsMargins(24, 24, 24, 24)
        total_inner.setSpacing(8)

        total_title = QLabel("TOTAL A PAYER")
        total_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        total_inner.addWidget(total_title)

        self.total_label = QLabel("0 FCFA")
        self.total_label.setStyleSheet("color: #000000; font-size: 40px; font-weight: 700; letter-spacing: -1px;")
        total_inner.addWidget(self.total_label)

        self.tax_info = QLabel("TVA incluse")
        self.tax_info.setStyleSheet("color: #888888; font-size: 12px;")
        total_inner.addWidget(self.tax_info)

        right_layout.addWidget(total_card)

        # Main pay button - Black Vercel style
        self.pay_button = QPushButton("Valider le paiement")
        self.pay_button.setMinimumHeight(60)
        self.pay_button.setStyleSheet("""
            QPushButton {
                background: #000000;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover { background: #333333; }
            QPushButton:pressed { background: #1A1A1A; }
        """)
        self.pay_button.clicked.connect(self._open_payment)
        right_layout.addWidget(self.pay_button)

        # Summary card
        summary_card = QFrame()
        summary_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EAEAEA;
                border-radius: 12px;
            }
        """)
        summary_inner = QVBoxLayout(summary_card)
        summary_inner.setContentsMargins(20, 16, 20, 16)
        summary_inner.setSpacing(12)

        summary_title = QLabel("RESUME")
        summary_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        summary_inner.addWidget(summary_title)

        # Subtotal
        row1 = QHBoxLayout()
        row1_lbl = QLabel("Sous-total")
        row1_lbl.setStyleSheet("color: #666666; font-size: 14px;")
        self.subtotal_lbl = QLabel("0 FCFA")
        self.subtotal_lbl.setStyleSheet("color: #000000; font-size: 14px; font-weight: 500;")
        row1.addWidget(row1_lbl)
        row1.addStretch()
        row1.addWidget(self.subtotal_lbl)
        summary_inner.addLayout(row1)

        # TVA
        row2 = QHBoxLayout()
        row2_lbl = QLabel("TVA")
        row2_lbl.setStyleSheet("color: #666666; font-size: 14px;")
        self.tax_lbl = QLabel("0 FCFA")
        self.tax_lbl.setStyleSheet("color: #000000; font-size: 14px; font-weight: 500;")
        row2.addWidget(row2_lbl)
        row2.addStretch()
        row2.addWidget(self.tax_lbl)
        summary_inner.addLayout(row2)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #EAEAEA;")
        summary_inner.addWidget(div)

        # Total
        row3 = QHBoxLayout()
        row3_lbl = QLabel("Total")
        row3_lbl.setStyleSheet("color: #000000; font-size: 15px; font-weight: 600;")
        self.final_total_lbl = QLabel("0 FCFA")
        self.final_total_lbl.setStyleSheet("color: #000000; font-size: 16px; font-weight: 700;")
        row3.addWidget(row3_lbl)
        row3.addStretch()
        row3.addWidget(self.final_total_lbl)
        summary_inner.addLayout(row3)

        right_layout.addWidget(summary_card)

        # Pending sales section
        pending_title = QLabel("VENTES EN ATTENTE")
        pending_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; letter-spacing: 1px; padding-top: 8px;")
        right_layout.addWidget(pending_title)

        self.pending_frame = QFrame()
        self.pending_frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EAEAEA;
                border-radius: 12px;
            }
        """)
        self.pending_layout = QVBoxLayout(self.pending_frame)
        self.pending_layout.setContentsMargins(16, 12, 16, 12)
        self.pending_layout.setSpacing(8)

        self.pending_placeholder = QLabel("Aucune vente en attente")
        self.pending_placeholder.setStyleSheet("color: #A3A3A3; font-size: 13px; padding: 8px 0;")
        self.pending_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pending_layout.addWidget(self.pending_placeholder)

        right_layout.addWidget(self.pending_frame)
        right_layout.addStretch()

        body_layout.addWidget(right)
        root.addWidget(body, 1)

        # Keyboard shortcuts
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        QShortcut(QKeySequence("F3"), self).activated.connect(self._remove_last_product)
        QShortcut(QKeySequence("F4"), self).activated.connect(self._hold_current_sale)

        # Barcode scanner timer
        self._scanner_buffer = ""
        self._scanner_timer = QTimer(self)
        self._scanner_timer.timeout.connect(self._flush_scanner_buffer)
        self._scanner_timer.setSingleShot(True)

        self.scan_input.setFocus()
        self._update_totals()
        self._update_pending_display()

    def _scan_product(self) -> None:
        barcode = self.scan_input.text().strip()
        self.scan_input.clear()
        if not barcode:
            return
        line = self.sale_service.add_product_to_cart(barcode, 1)
        if line:
            self._merge_or_add_line(line)
            self._refresh_cart()
        else:
            QMessageBox.warning(self, "Produit introuvable", f"Aucun produit avec le code: {barcode}")

    def _merge_or_add_line(self, new_line: CartLine) -> None:
        for existing in self.cart_lines:
            if existing.product.id == new_line.product.id:
                existing.quantity += new_line.quantity
                return
        self.cart_lines.append(new_line)

    def _refresh_cart(self) -> None:
        self.cart_widget.set_lines(self.cart_lines)
        self._update_totals()

    def _update_totals(self) -> None:
        subtotal = sum((line.total_price for line in self.cart_lines), Decimal("0.00"))
        tax = sum((line.product.tax_rate or Decimal("0")) * line.total_price / 100 for line in self.cart_lines)
        
        if self.discount_percent > 0:
            discount = (subtotal * self.discount_percent / 100).quantize(Decimal("0.01"))
            subtotal -= discount
            tax = (tax * (1 - self.discount_percent / 100)).quantize(Decimal("0.01"))

        total = subtotal + tax
        item_count = sum(line.quantity for line in self.cart_lines)

        self.total_label.setText(f"{total:,.0f} FCFA")
        self.subtotal_lbl.setText(f"{subtotal:,.0f} FCFA")
        self.tax_lbl.setText(f"{tax:,.0f} FCFA")
        self.final_total_lbl.setText(f"{total:,.0f} FCFA")
        self.cart_count.setText(f"{item_count} article{'s' if item_count > 1 else ''}")

    def _remove_last_product(self) -> None:
        if self.cart_lines:
            self.cart_lines.pop()
            self._refresh_cart()

    def _clear_cart(self) -> None:
        if not self.cart_lines:
            return
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment vider le panier?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cart_lines.clear()
            self.discount_percent = Decimal("0")
            self._refresh_cart()

    def _hold_current_sale(self) -> None:
        if not self.cart_lines:
            return
        pending = PendingSale(
            ticket_id=self.pending_sale_counter,
            created_at=datetime.now(),
            lines=deepcopy(self.cart_lines),
            discount_percent=self.discount_percent,
        )
        self.pending_sales.append(pending)
        self.pending_sale_counter += 1
        self.cart_lines.clear()
        self.discount_percent = Decimal("0")
        self._refresh_cart()
        self._update_pending_display()

    def _update_pending_display(self) -> None:
        # Clear existing
        while self.pending_layout.count():
            item = self.pending_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.pending_sales:
            self.pending_placeholder = QLabel("Aucune vente en attente")
            self.pending_placeholder.setStyleSheet("color: #A3A3A3; font-size: 13px; padding: 8px 0;")
            self.pending_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pending_layout.addWidget(self.pending_placeholder)
            return

        for sale in self.pending_sales:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row_layout.setSpacing(8)

            info = QLabel(f"Ticket #{sale.ticket_id} - {sale.item_count} articles")
            info.setStyleSheet("color: #000000; font-size: 13px; font-weight: 500;")
            row_layout.addWidget(info)
            row_layout.addStretch()

            total_lbl = QLabel(f"{sale.total:,.0f}")
            total_lbl.setStyleSheet("color: #666666; font-size: 13px;")
            row_layout.addWidget(total_lbl)

            restore_btn = QPushButton("Reprendre")
            restore_btn.setStyleSheet("""
                QPushButton {
                    background: #F5F5F5;
                    color: #000000;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 10px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover { background: #EAEAEA; }
            """)
            restore_btn.clicked.connect(lambda checked, s=sale: self._restore_pending(s))
            row_layout.addWidget(restore_btn)

            self.pending_layout.addWidget(row)

    def _restore_pending(self, sale: PendingSale) -> None:
        if self.cart_lines:
            reply = QMessageBox.question(
                self, "Confirmation",
                "Le panier actuel sera remplace. Continuer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.cart_lines = deepcopy(sale.lines)
        self.discount_percent = sale.discount_percent
        self.pending_sales.remove(sale)
        self._refresh_cart()
        self._update_pending_display()

    def _open_payment(self, channel: str | None = None) -> None:
        if not self.cart_lines:
            QMessageBox.information(self, "Panier vide", "Ajoutez des produits avant de payer.")
            return

        total = sum((line.total_price for line in self.cart_lines), Decimal("0.00"))
        if self.discount_percent > 0:
            total -= (total * self.discount_percent / 100).quantize(Decimal("0.01"))

        dialog = PaymentDialog(total, self)
        if channel:
            dialog.set_channel(channel)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            amount_received = dialog.get_amount_received()
            payment_channel = dialog.get_channel()
            self._finalize_sale(total, amount_received, payment_channel)

    def _finalize_sale(self, total: Decimal, received: Decimal, channel: str) -> None:
        try:
            sale = self.sale_service.create_sale(
                lines=self.cart_lines,
                cashier_id=self.cashier.id,
                discount_percent=self.discount_percent,
                amount_received=received,
                payment_channel=channel,
            )

            receipt_text = self.receipt_service.generate_receipt(
                sale=sale,
                lines=self.cart_lines,
                cashier_name=f"{self.cashier.prenom} {self.cashier.nom}",
                amount_received=received,
                change=received - total,
            )

            preview = ReceiptPreview(receipt_text, self)
            preview.exec()

            self.cart_lines.clear()
            self.discount_percent = Decimal("0")
            self._refresh_cart()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de finaliser la vente:\n{e}")

    def _flush_scanner_buffer(self) -> None:
        if self._scanner_buffer:
            self.scan_input.setText(self._scanner_buffer)
            self._scan_product()
            self._scanner_buffer = ""

    def keyPressEvent(self, event) -> None:
        # Handle barcode scanner input
        if event.text() and event.text().isprintable():
            self._scanner_buffer += event.text()
            self._scanner_timer.start(50)
        super().keyPressEvent(event)
