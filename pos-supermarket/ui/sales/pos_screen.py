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
        self.held_sale_lines: list[CartLine] = []

        self.setWindowTitle("MOKAT MARKET — Caisse")
        self.resize(1280, 820)
        self.setStyleSheet("font-family: 'Segoe UI', 'Inter', sans-serif;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background: #0F172A; border: none;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(16)

        # Logo badge
        logo = QLabel("M")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            "background: #2563EB; color: #FFFFFF; font-size: 15px; font-weight: 800;"
            "border-radius: 8px;"
        )
        header_layout.addWidget(logo)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        brand_name = QLabel("MOKAT MARKET")
        brand_name.setStyleSheet(
            "color: #FFFFFF; font-size: 13px; font-weight: 700; letter-spacing: 1px;"
        )
        brand_sub = QLabel("Point de Vente")
        brand_sub.setStyleSheet("color: #475569; font-size: 11px;")
        brand_col.addWidget(brand_name)
        brand_col.addWidget(brand_sub)
        header_layout.addLayout(brand_col)
        header_layout.addStretch()

        # Session info
        session_lbl = QLabel("Session ouverte")
        session_lbl.setStyleSheet(
            "color: #10B981; font-size: 12px; font-weight: 600;"
            "background: rgba(16,185,129,0.12); border-radius: 10px; padding: 4px 12px;"
        )
        header_layout.addWidget(session_lbl)

        # Cashier avatar
        initials = ""
        if cashier.prenom:
            initials += cashier.prenom[0].upper()
        if cashier.nom:
            initials += cashier.nom[0].upper()
        cashier_avatar = QLabel(initials or "?")
        cashier_avatar.setFixedSize(34, 34)
        cashier_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cashier_avatar.setStyleSheet(
            "background: #3B82F6; color: #FFFFFF; border-radius: 17px;"
            "font-size: 12px; font-weight: 700;"
        )
        cashier_name = QLabel(f"{cashier.prenom} {cashier.nom}")
        cashier_name.setStyleSheet("color: #CBD5E1; font-size: 13px; font-weight: 500;")
        header_layout.addWidget(cashier_avatar)
        header_layout.addWidget(cashier_name)

        root.addWidget(header)

        # ══════════════════════════════════════════════════════
        # BODY
        # ══════════════════════════════════════════════════════
        body = QWidget()
        body.setStyleSheet("background: #F1F5F9;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 18)
        body_layout.setSpacing(18)

        # ─────────────────────────────────────────────────────
        # LEFT — Scanner + Panier (flex 1)
        # ─────────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        # ---- Scan card ----
        scan_card = QFrame()
        scan_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 2px solid #2563EB; border-radius: 14px; }"
        )
        scan_inner = QVBoxLayout(scan_card)
        scan_inner.setContentsMargins(20, 16, 20, 16)
        scan_inner.setSpacing(10)

        scan_top = QHBoxLayout()
        scan_tag = QLabel("SCANNER")
        scan_tag.setStyleSheet(
            "color: #2563EB; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
            "background: #EFF6FF; border-radius: 6px; padding: 4px 10px;"
        )
        scan_title = QLabel("Saisir ou scanner un produit")
        scan_title.setStyleSheet(
            "color: #0F172A; font-size: 14px; font-weight: 600; margin-left: 10px;"
        )
        scan_top.addWidget(scan_tag)
        scan_top.addWidget(scan_title)
        scan_top.addStretch()
        scan_inner.addLayout(scan_top)

        self.scan_input = QLineEdit()
        self.scan_input.setObjectName("ScanInput")
        self.scan_input.setPlaceholderText("Code-barres  —  appuyez sur Entree pour ajouter")
        self.scan_input.returnPressed.connect(self._scan_product)
        scan_inner.addWidget(self.scan_input)

        left_layout.addWidget(scan_card)

        # ---- Cart card ----
        cart_card = QFrame()
        cart_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; }"
        )
        cart_inner = QVBoxLayout(cart_card)
        cart_inner.setContentsMargins(20, 16, 20, 16)
        cart_inner.setSpacing(10)

        cart_top = QHBoxLayout()
        cart_title = QLabel("Panier")
        cart_title.setStyleSheet("color: #0F172A; font-size: 15px; font-weight: 700;")
        self.cart_count = QLabel("0 article")
        self.cart_count.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 500;"
            "background: #F1F5F9; border-radius: 8px; padding: 4px 10px;"
        )
        cart_top.addWidget(cart_title)
        cart_top.addStretch()
        cart_top.addWidget(self.cart_count)
        cart_top_w = QWidget()
        cart_top_w.setLayout(cart_top)
        cart_inner.addWidget(cart_top_w)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #F1F5F9;")
        cart_inner.addWidget(sep)

        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cart_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: #F1F5F9; width: 8px; border-radius: 4px; }"
            "QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 4px; min-height: 30px; }"
            "QScrollBar::handle:vertical:hover { background: #94A3B8; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        self.cart_widget = CartWidget()
        cart_scroll.setWidget(self.cart_widget)
        cart_inner.addWidget(cart_scroll, 1)

        left_layout.addWidget(cart_card, 1)
        body_layout.addWidget(left, 1)

        # ─────────────────────────────────────────────────────
        # RIGHT — Total + Actions (fixed 360px)
        # ─────────────────────────────────────────────────────
        right = QWidget()
        right.setFixedWidth(360)
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        # ---- Total card ----
        total_card = QFrame()
        total_card.setStyleSheet(
            "QFrame { background: #0F172A; border-radius: 18px; border: none; }"
        )
        total_inner = QVBoxLayout(total_card)
        total_inner.setContentsMargins(24, 22, 24, 22)
        total_inner.setSpacing(6)

        total_title = QLabel("TOTAL A PAYER")
        total_title.setStyleSheet(
            "color: #475569; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;"
        )
        total_inner.addWidget(total_title)

        self.total_label = QLabel("0 FCFA")
        self.total_label.setObjectName("TotalLarge")
        self.total_label.setStyleSheet(
            "color: #FFFFFF; font-size: 38px; font-weight: 800; letter-spacing: -1px;"
        )
        total_inner.addWidget(self.total_label)

        self.tax_info = QLabel("TVA incluse")
        self.tax_info.setStyleSheet("color: #334155; font-size: 11px;")
        total_inner.addWidget(self.tax_info)

        right_layout.addWidget(total_card)

        # ---- Pay button ----
        self.pay_button = QPushButton("Valider le paiement")
        self.pay_button.setMinimumHeight(56)
        self.pay_button.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover { background: #047857; }
            QPushButton:pressed { background: #065F46; }
        """)
        self.pay_button.clicked.connect(self._open_payment)
        right_layout.addWidget(self.pay_button)

        # ---- Quick payment ----
        quick_card = QFrame()
        quick_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; }"
        )
        quick_inner = QVBoxLayout(quick_card)
        quick_inner.setContentsMargins(18, 16, 18, 16)
        quick_inner.setSpacing(10)

        quick_lbl = QLabel("Paiement rapide")
        quick_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
        )
        quick_inner.addWidget(quick_lbl)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(10)

        self.cash_btn = QPushButton("F1   Especes")
        self.cash_btn.setMinimumHeight(46)
        self.cash_btn.setStyleSheet("""
            QPushButton {
                background: #F8FAFC; color: #1E293B;
                border: 1.5px solid #E2E8F0; border-radius: 10px;
                font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; }
        """)
        self.cash_btn.clicked.connect(
            lambda: self._open_payment(PaymentService.CASH_CHANNEL)
        )

        self.mobile_btn = QPushButton("F2   Mobile")
        self.mobile_btn.setMinimumHeight(46)
        self.mobile_btn.setStyleSheet("""
            QPushButton {
                background: #EFF6FF; color: #1D4ED8;
                border: 1.5px solid #BFDBFE; border-radius: 10px;
                font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: #DBEAFE; }
        """)
        self.mobile_btn.clicked.connect(
            lambda: self._open_payment(PaymentService.WAVE_CHANNEL)
        )

        quick_grid.addWidget(self.cash_btn, 0, 0)
        quick_grid.addWidget(self.mobile_btn, 0, 1)
        quick_inner.addLayout(quick_grid)
        right_layout.addWidget(quick_card)

        # ---- Actions card ----
        actions_card = QFrame()
        actions_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; }"
        )
        actions_inner = QVBoxLayout(actions_card)
        actions_inner.setContentsMargins(18, 16, 18, 16)
        actions_inner.setSpacing(8)

        actions_lbl = QLabel("Actions")
        actions_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;"
        )
        actions_inner.addWidget(actions_lbl)

        self.remove_btn = QPushButton("F3   Supprimer dernier article")
        self.remove_btn.setMinimumHeight(42)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #FEF2F2; color: #DC2626;
                border: 1px solid #FECACA; border-radius: 10px;
                font-size: 13px; font-weight: 600; text-align: left; padding-left: 14px;
            }
            QPushButton:hover { background: #FEE2E2; }
        """)
        self.remove_btn.clicked.connect(self._remove_last_product)
        actions_inner.addWidget(self.remove_btn)

        self.hold_btn = QPushButton("F4   Mettre en attente")
        self.hold_btn.setMinimumHeight(42)
        self.hold_btn.setStyleSheet("""
            QPushButton {
                background: #FFFBEB; color: #D97706;
                border: 1px solid #FDE68A; border-radius: 10px;
                font-size: 13px; font-weight: 600; text-align: left; padding-left: 14px;
            }
            QPushButton:hover { background: #FEF3C7; }
        """)
        self.hold_btn.clicked.connect(self._hold_current_sale)
        actions_inner.addWidget(self.hold_btn)

        self.clear_btn = QPushButton("Vider le panier")
        self.clear_btn.setMinimumHeight(42)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #F8FAFC; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 10px;
                font-size: 13px; font-weight: 600; text-align: left; padding-left: 14px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        self.clear_btn.clicked.connect(self._clear_cart)
        actions_inner.addWidget(self.clear_btn)

        right_layout.addWidget(actions_card)
        right_layout.addStretch()

        # Keyboard shortcuts hint
        shortcuts_lbl = QLabel("F1 Especes   F2 Mobile   F3 Annuler   F4 Attente")
        shortcuts_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; padding: 6px 0;"
        )
        right_layout.addWidget(shortcuts_lbl)

        body_layout.addWidget(right)
        root.addWidget(body, 1)

        self.preview = ReceiptPreview()
        self._install_shortcuts()
        QTimer.singleShot(0, self._focus_scan_input)

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:  # type: ignore[override]
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
        self.total_label.setText(f"{int(total):,} FCFA")
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
