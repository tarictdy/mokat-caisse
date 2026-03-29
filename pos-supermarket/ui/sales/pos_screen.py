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
    """Interface de caisse moderne et fluide"""
    
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

        self.setWindowTitle("MOKAT MARKET — Caisse")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QWidget {
                font-family: "Segoe UI", "Inter", sans-serif;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════════════════════
        # HEADER - Barre superieure
        # ══════════════════════════════════════════════════════════════════════
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F172A, stop:1 #1E293B);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        header_layout.setSpacing(16)

        # Logo
        logo = QLabel("M")
        logo.setFixedSize(38, 38)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #3B82F6, stop:1 #1D4ED8);
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 800;
            border-radius: 8px;
        """)
        header_layout.addWidget(logo)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_name = QLabel("MOKAT MARKET")
        brand_name.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        brand_sub = QLabel("Point de Vente")
        brand_sub.setStyleSheet("color: #64748B; font-size: 11px;")
        brand_text.addWidget(brand_name)
        brand_text.addWidget(brand_sub)
        header_layout.addLayout(brand_text)
        header_layout.addStretch()

        # Status indicators
        status_container = QHBoxLayout()
        status_container.setSpacing(20)

        # Connection status
        conn_status = QLabel("Connecte")
        conn_status.setStyleSheet("""
            color: #10B981;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 12px;
            background: rgba(16, 185, 129, 0.15);
            border-radius: 12px;
        """)
        status_container.addWidget(conn_status)

        # Cashier info
        cashier_avatar = QLabel(f"{cashier.prenom[0]}{cashier.nom[0]}")
        cashier_avatar.setFixedSize(36, 36)
        cashier_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cashier_avatar.setStyleSheet("""
            background: #3B82F6;
            color: #FFFFFF;
            border-radius: 18px;
            font-size: 12px;
            font-weight: 700;
        """)
        status_container.addWidget(cashier_avatar)

        cashier_name = QLabel(f"{cashier.prenom} {cashier.nom}")
        cashier_name.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: 600;")
        status_container.addWidget(cashier_name)

        header_layout.addLayout(status_container)
        root.addWidget(header)

        # ══════════════════════════════════════════════════════════════════════
        # MAIN BODY - Zone principale
        # ══════════════════════════════════════════════════════════════════════
        body = QWidget()
        body.setStyleSheet("background: #F1F5F9;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)
        body_layout.setSpacing(20)

        # ──────────────────────────────────────────────────────────────────────
        # LEFT COLUMN - Scanner + Panier (60%)
        # ──────────────────────────────────────────────────────────────────────
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # Scanner Card
        scan_card = QFrame()
        scan_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 2px solid #3B82F6;
                border-radius: 16px;
            }
        """)
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(24, 20, 24, 20)
        scan_layout.setSpacing(12)

        scan_header = QHBoxLayout()
        scan_icon = QLabel("Scan")
        scan_icon.setStyleSheet("""
            background: #EFF6FF;
            color: #3B82F6;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 6px;
        """)
        scan_title = QLabel("Scanner un produit")
        scan_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; margin-left: 12px;")
        scan_header.addWidget(scan_icon)
        scan_header.addWidget(scan_title)
        scan_header.addStretch()
        scan_layout.addLayout(scan_header)

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Scannez ou saisissez le code-barres...")
        self.scan_input.returnPressed.connect(self._scan_product)
        self.scan_input.setMinimumHeight(56)
        self.scan_input.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 0 20px;
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
                background: #FFFFFF;
            }
        """)
        scan_layout.addWidget(self.scan_input)
        left_layout.addWidget(scan_card)

        # Cart Card
        cart_card = QFrame()
        cart_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(24, 20, 24, 20)
        cart_layout.setSpacing(12)

        cart_header = QHBoxLayout()
        cart_title = QLabel("Panier")
        cart_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        self.cart_count = QLabel("0 articles")
        self.cart_count.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            font-weight: 500;
            background: #F1F5F9;
            padding: 6px 12px;
            border-radius: 8px;
        """)
        cart_header.addWidget(cart_title)
        cart_header.addStretch()
        cart_header.addWidget(self.cart_count)
        cart_layout.addWidget(self._header_widget(cart_header))

        # Cart with scroll
        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cart_scroll.setStyleSheet("""
            QScrollArea { 
                background: transparent; 
                border: none; 
            }
            QScrollBar:vertical {
                background: #F1F5F9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
        """)
        
        self.cart_widget = CartWidget()
        cart_scroll.setWidget(self.cart_widget)
        cart_layout.addWidget(cart_scroll, 1)
        left_layout.addWidget(cart_card, 1)

        body_layout.addWidget(left_container, 6)

        # ──────────────────────────────────────────────────────────────────────
        # RIGHT COLUMN - Total + Actions (40%)
        # ──────────────────────────────────────────────────────────────────────
        right_container = QWidget()
        right_container.setFixedWidth(380)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Total Card
        total_card = QFrame()
        total_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0F172A, stop:1 #1E293B);
                border-radius: 20px;
            }
        """)
        total_layout = QVBoxLayout(total_card)
        total_layout.setContentsMargins(28, 28, 28, 28)
        total_layout.setSpacing(8)

        total_title = QLabel("TOTAL A PAYER")
        total_title.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        total_layout.addWidget(total_title)

        self.total_label = QLabel("0 FCFA")
        self.total_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1px;
        """)
        total_layout.addWidget(self.total_label)

        # Tax info
        self.tax_info = QLabel("TVA incluse")
        self.tax_info.setStyleSheet("color: #64748B; font-size: 12px;")
        total_layout.addWidget(self.tax_info)

        right_layout.addWidget(total_card)

        # Payment Actions Card
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(12)

        # Main pay button
        self.pay_button = QPushButton("Valider le paiement")
        self.pay_button.setMinimumHeight(60)
        self.pay_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 17px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        self.pay_button.clicked.connect(self._open_payment)
        actions_layout.addWidget(self.pay_button)

        # Quick payment grid
        quick_label = QLabel("Paiement rapide")
        quick_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; margin-top: 8px;")
        actions_layout.addWidget(quick_label)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(10)

        self.cash_btn = QPushButton("F1  Especes")
        self.cash_btn.setMinimumHeight(48)
        self.cash_btn.setStyleSheet("""
            QPushButton {
                background: #F8FAFC;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E2E8F0;
                border-color: #CBD5E1;
            }
        """)
        self.cash_btn.clicked.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))

        self.mobile_btn = QPushButton("F2  Mobile")
        self.mobile_btn.setMinimumHeight(48)
        self.mobile_btn.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #DBEAFE;
            }
        """)
        self.mobile_btn.clicked.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))

        quick_grid.addWidget(self.cash_btn, 0, 0)
        quick_grid.addWidget(self.mobile_btn, 0, 1)
        actions_layout.addLayout(quick_grid)

        right_layout.addWidget(actions_card)

        # Utility Actions Card
        util_card = QFrame()
        util_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        util_layout = QVBoxLayout(util_card)
        util_layout.setContentsMargins(20, 20, 20, 20)
        util_layout.setSpacing(10)

        util_label = QLabel("Actions")
        util_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        util_layout.addWidget(util_label)

        self.remove_btn = QPushButton("F3  Supprimer dernier article")
        self.remove_btn.setMinimumHeight(44)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #FEE2E2;
            }
        """)
        self.remove_btn.clicked.connect(self._remove_last_product)
        util_layout.addWidget(self.remove_btn)

        self.hold_btn = QPushButton("F4  Mettre en attente")
        self.hold_btn.setMinimumHeight(44)
        self.hold_btn.setStyleSheet("""
            QPushButton {
                background: #FFFBEB;
                color: #D97706;
                border: 1px solid #FDE68A;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #FEF3C7;
            }
        """)
        self.hold_btn.clicked.connect(self._hold_current_sale)
        util_layout.addWidget(self.hold_btn)

        self.clear_btn = QPushButton("F5  Vider le panier")
        self.clear_btn.setMinimumHeight(44)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #F8FAFC;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E2E8F0;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_cart)
        util_layout.addWidget(self.clear_btn)

        self.discount_btn = QPushButton("F7  Reduction (%)")
        self.discount_btn.setMinimumHeight(44)
        self.discount_btn.setStyleSheet("""
            QPushButton {
                background: #ECFDF5;
                color: #047857;
                border: 1px solid #A7F3D0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #D1FAE5;
            }
        """)
        self.discount_btn.clicked.connect(self._request_discount)
        util_layout.addWidget(self.discount_btn)

        right_layout.addWidget(util_card)

        pending_card = QFrame()
        pending_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        pending_layout = QVBoxLayout(pending_card)
        pending_layout.setContentsMargins(16, 16, 16, 16)
        pending_layout.setSpacing(10)

        pending_header = QHBoxLayout()
        pending_title = QLabel("Ventes en attente")
        pending_title.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: 700;")
        self.pending_count_label = QLabel("0")
        self.pending_count_label.setStyleSheet("""
            color: #1D4ED8;
            background: #DBEAFE;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 8px;
        """)
        pending_header.addWidget(pending_title)
        pending_header.addStretch()
        pending_header.addWidget(self.pending_count_label)
        pending_layout.addLayout(pending_header)

        self.pending_scroll = QScrollArea()
        self.pending_scroll.setWidgetResizable(True)
        self.pending_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pending_scroll.setMinimumHeight(170)
        self.pending_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.pending_container = QWidget()
        self.pending_sales_layout = QVBoxLayout(self.pending_container)
        self.pending_sales_layout.setContentsMargins(0, 0, 0, 0)
        self.pending_sales_layout.setSpacing(8)
        self.pending_sales_layout.addStretch()
        self.pending_scroll.setWidget(self.pending_container)

        pending_layout.addWidget(self.pending_scroll)
        right_layout.addWidget(pending_card)
        right_layout.addStretch()

        # Shortcuts hint
        shortcuts_lbl = QLabel("F1 Especes | F2 Mobile | F3 Supprimer | F4 Attente | F5 Vider | F6 Scan | F7 Reduction | Ctrl+P Payer | Ctrl+1 Charger attente | Ctrl+2 Payer attente")
        shortcuts_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_lbl.setStyleSheet("""
            color: #94A3B8;
            font-size: 11px;
            padding: 8px;
        """)
        right_layout.addWidget(shortcuts_lbl)

        body_layout.addWidget(right_container)
        root.addWidget(body, 1)

        self.preview = ReceiptPreview()
        self._refresh_pending_sales_panel()
        self._install_shortcuts()
        QTimer.singleShot(0, self._focus_scan_input)

    def _header_widget(self, layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._focus_scan_input()

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: self._open_payment(PaymentService.CASH_CHANNEL))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self._open_payment(PaymentService.WAVE_CHANNEL))
        QShortcut(QKeySequence("F3"), self).activated.connect(self._remove_last_product)
        QShortcut(QKeySequence("F4"), self).activated.connect(self._hold_current_sale)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._clear_cart)
        QShortcut(QKeySequence("F6"), self).activated.connect(self._focus_scan_input)
        QShortcut(QKeySequence("F7"), self).activated.connect(self._request_discount)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self._open_payment)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._hold_current_sale)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._remove_last_product)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._clear_cart)
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(self._load_first_pending_sale)
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(self._pay_first_pending_sale)

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

    def _clear_cart(self) -> None:
        if not self.cart_lines:
            return
        if QMessageBox.question(
            self, "Confirmation", "Voulez-vous vider le panier ?"
        ) == QMessageBox.StandardButton.Yes:
            self.cart_lines = []
            self.cart_widget.load_lines(self.cart_lines)
            self._refresh_total()
        self._focus_scan_input()

    def _hold_current_sale(self) -> None:
        if not self.cart_lines:
            return

        pending_sale = PendingSale(
            ticket_id=self.pending_sale_counter,
            created_at=datetime.now(),
            lines=deepcopy(self.cart_lines),
            discount_percent=self.discount_percent,
        )
        self.pending_sale_counter += 1
        self.pending_sales.append(pending_sale)

        self.cart_lines = []
        self.discount_percent = Decimal("0")
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        self._refresh_pending_sales_panel()
        QMessageBox.information(self, "Vente en attente", "La vente en cours a ete mise en attente.")
        self._focus_scan_input()

    def _refresh_pending_sales_panel(self) -> None:
        while self.pending_sales_layout.count():
            item = self.pending_sales_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.pending_count_label.setText(str(len(self.pending_sales)))

        if not self.pending_sales:
            empty_label = QLabel("Aucune vente en attente")
            empty_label.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 8px;")
            self.pending_sales_layout.addWidget(empty_label)
            self.pending_sales_layout.addStretch()
            return

        for sale in self.pending_sales:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(6)

            top_row = QHBoxLayout()
            title = QLabel(f"Ticket attente #{sale.ticket_id}")
            title.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 700;")
            time_lbl = QLabel(sale.created_at.strftime("%H:%M"))
            time_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
            top_row.addWidget(title)
            top_row.addStretch()
            top_row.addWidget(time_lbl)
            card_layout.addLayout(top_row)

            details = QLabel(f"{sale.item_count} articles  •  {int(sale.total):,} FCFA")
            details.setStyleSheet("color: #475569; font-size: 12px;")
            card_layout.addWidget(details)

            actions = QHBoxLayout()
            actions.setSpacing(6)

            load_btn = QPushButton("Charger")
            load_btn.setStyleSheet("QPushButton { background: #E2E8F0; border: none; border-radius: 8px; padding: 6px; font-size: 11px; }")
            load_btn.clicked.connect(lambda _, sid=sale.ticket_id: self._load_pending_sale(sid))
            actions.addWidget(load_btn)

            pay_btn = QPushButton("Payer")
            pay_btn.setStyleSheet("QPushButton { background: #DCFCE7; color: #166534; border: none; border-radius: 8px; padding: 6px; font-size: 11px; font-weight: 700; }")
            pay_btn.clicked.connect(lambda _, sid=sale.ticket_id: self._pay_pending_sale(sid))
            actions.addWidget(pay_btn)

            delete_btn = QPushButton("Suppr.")
            delete_btn.setStyleSheet("QPushButton { background: #FEE2E2; color: #B91C1C; border: none; border-radius: 8px; padding: 6px; font-size: 11px; }")
            delete_btn.clicked.connect(lambda _, sid=sale.ticket_id: self._remove_pending_sale(sid))
            actions.addWidget(delete_btn)

            card_layout.addLayout(actions)
            self.pending_sales_layout.addWidget(card)

        self.pending_sales_layout.addStretch()

    def _find_pending_sale(self, ticket_id: int) -> PendingSale | None:
        return next((sale for sale in self.pending_sales if sale.ticket_id == ticket_id), None)

    def _load_pending_sale(self, ticket_id: int) -> None:
        pending = self._find_pending_sale(ticket_id)
        if pending is None:
            return

        if self.cart_lines and QMessageBox.question(
            self,
            "Charger une vente",
            "Le panier actuel sera remplace. Continuer ?",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.cart_lines = deepcopy(pending.lines)
        self.discount_percent = pending.discount_percent
        self.pending_sales = [sale for sale in self.pending_sales if sale.ticket_id != ticket_id]
        self.cart_widget.load_lines(self.cart_lines)
        self._refresh_total()
        self._refresh_pending_sales_panel()
        self._focus_scan_input()

    def _remove_pending_sale(self, ticket_id: int) -> None:
        self.pending_sales = [sale for sale in self.pending_sales if sale.ticket_id != ticket_id]
        self._refresh_pending_sales_panel()
        self._focus_scan_input()

    def _pay_pending_sale(self, ticket_id: int) -> None:
        pending = self._find_pending_sale(ticket_id)
        if pending is None:
            return

        if self._checkout_lines(deepcopy(pending.lines), discount_percent=pending.discount_percent):
            self.pending_sales = [sale for sale in self.pending_sales if sale.ticket_id != ticket_id]
            self._refresh_pending_sales_panel()

        self._focus_scan_input()

    def _load_first_pending_sale(self) -> None:
        if not self.pending_sales:
            return
        self._load_pending_sale(self.pending_sales[0].ticket_id)

    def _pay_first_pending_sale(self) -> None:
        if not self.pending_sales:
            return
        self._pay_pending_sale(self.pending_sales[0].ticket_id)

    def _refresh_total(self) -> Decimal:
        subtotal = self.sale_service.compute_total(self.cart_lines)
        discount_amount = self._compute_discount_amount(subtotal, self.discount_percent)
        total = subtotal - discount_amount
        self.total_label.setText(f"{int(total):,} FCFA")
        self.cart_count.setText(f"{len(self.cart_lines)} article{'s' if len(self.cart_lines) != 1 else ''}")
        if discount_amount > 0:
            self.tax_info.setText(
                f"Reduction {self._format_decimal(self.discount_percent)}% (-{int(discount_amount):,} FCFA) • TVA incluse"
            )
        else:
            self.tax_info.setText("TVA incluse")
        return total

    def _open_payment(self, preferred_channel: str | None = None) -> None:
        if self._checkout_lines(self.cart_lines, preferred_channel, self.discount_percent):
            self.cart_lines = []
            self.discount_percent = Decimal("0")
            self.cart_widget.load_lines(self.cart_lines)
            self._refresh_total()
        self._focus_scan_input()

    def _checkout_lines(
        self,
        lines: list[CartLine],
        preferred_channel: str | None = None,
        discount_percent: Decimal = Decimal("0"),
    ) -> bool:
        subtotal = self.sale_service.compute_total(lines)
        discount_amount = self._compute_discount_amount(subtotal, discount_percent)
        total = subtotal - discount_amount
        if total <= 0:
            QMessageBox.information(self, "Panier vide", "Scannez au moins un produit avant de payer.")
            return False

        dialog = PaymentDialog(total, self)
        if preferred_channel:
            dialog.set_preferred_channel(preferred_channel)

        if dialog.exec() != PaymentDialog.DialogCode.Accepted:
            return False

        sale = self.sale_service.finalize_sale(
            self.cashier,
            dialog.selected_method,
            dialog.selected_channel,
            lines,
            dialog.transaction_reference,
            discount_amount=discount_amount,
        )
        receipt = self.receipt_service.build_receipt_text(
            sale, self.cashier, dialog.amount_given, dialog.change, lines
        )
        self.printer_service.print_and_cut(
            receipt,
            open_drawer=self.payment_service.is_cash_payment(dialog.selected_channel),
        )
        self.preview.set_receipt(receipt)
        self.preview.show()
        return True

    def _compute_discount_amount(self, subtotal: Decimal, discount_percent: Decimal) -> Decimal:
        if subtotal <= 0 or discount_percent <= 0:
            return Decimal("0.00")
        discount_amount = (subtotal * discount_percent / Decimal("100")).quantize(Decimal("0.01"))
        return max(Decimal("0.00"), min(discount_amount, subtotal))

    def _format_decimal(self, value: Decimal) -> str:
        normalized = value.normalize()
        return format(normalized, "f").rstrip("0").rstrip(".") if "." in format(normalized, "f") else format(normalized, "f")

    def _request_discount(self) -> None:
        if not self.cart_lines:
            QMessageBox.information(self, "Panier vide", "Ajoutez des produits avant d'appliquer une reduction.")
            self._focus_scan_input()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Reduction avec validation administrateur")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        percent_input = QLineEdit()
        percent_input.setPlaceholderText("Ex: 10")
        percent_input.setText(self._format_decimal(self.discount_percent) if self.discount_percent > 0 else "")
        form.addRow("Reduction (%)", percent_input)

        username_input = QLineEdit()
        username_input.setPlaceholderText("Compte administrateur")
        form.addRow("Utilisateur admin", username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("Mot de passe administrateur")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Mot de passe admin", password_input)
        layout.addLayout(form)

        actions = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn = QPushButton("Valider")
        confirm_btn.clicked.connect(dialog.accept)
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(confirm_btn)
        layout.addLayout(actions)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._focus_scan_input()
            return

        try:
            reduction_percent = Decimal(percent_input.text().strip())
        except InvalidOperation:
            QMessageBox.warning(self, "Reduction invalide", "Le pourcentage de reduction n'est pas valide.")
            self._focus_scan_input()
            return

        if reduction_percent < 0 or reduction_percent > 100:
            QMessageBox.warning(self, "Reduction invalide", "Le pourcentage doit etre compris entre 0 et 100.")
            self._focus_scan_input()
            return

        username = username_input.text().strip()
        password = password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Champs manquants", "Renseignez le compte et le mot de passe administrateur.")
            self._focus_scan_input()
            return

        with SessionLocal() as session:
            user_service = UserService(UserRepository(session))
            admin_user = user_service.authenticate(username, password)

        if not admin_user or admin_user.role != UserRole.ADMIN:
            QMessageBox.warning(self, "Validation refusee", "Compte administrateur invalide.")
            self._focus_scan_input()
            return

        self.discount_percent = reduction_percent.quantize(Decimal("0.01"))
        self._refresh_total()
        QMessageBox.information(
            self,
            "Reduction appliquee",
            f"Reduction de {self._format_decimal(self.discount_percent)}% appliquee avec validation administrateur.",
        )
        self._focus_scan_input()
