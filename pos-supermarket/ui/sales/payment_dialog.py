from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.sale import PaymentMethod
from services.payment_service import PaymentService


class PaymentDialog(QDialog):
    """Dialogue de paiement moderne et intuitif"""
    
    def __init__(self, total: Decimal, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.total = total
        self.payment_service = PaymentService()
        self.amount_given = Decimal("0")
        self.change = Decimal("0")
        self.selected_channel = PaymentService.CASH_CHANNEL
        self.selected_method = PaymentMethod.CASH
        self.transaction_reference = ""

        self.setWindowTitle("Encaissement")
        self.setMinimumSize(480, 580)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background: #F8FAFC;
            }
            QLabel {
                color: #374151;
            }
            QLineEdit, QComboBox {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 14px 16px;
                font-size: 14px;
                color: #1F2937;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #3B82F6;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 16px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 24, 28, 20)
        
        header_title = QLabel("Encaissement")
        header_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        header_layout.addWidget(header_title)
        layout.addWidget(header)

        # ── Content ───────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(20)

        # Total display card
        total_card = QFrame()
        total_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3B82F6, stop:1 #1D4ED8);
                border-radius: 16px;
            }
        """)
        total_card_layout = QVBoxLayout(total_card)
        total_card_layout.setContentsMargins(24, 24, 24, 24)
        total_card_layout.setSpacing(4)

        total_label_title = QLabel("TOTAL A PAYER")
        total_label_title.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        self.total_label = QLabel(f"{int(total):,} FCFA")
        self.total_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 36px;
            font-weight: 800;
        """)
        total_card_layout.addWidget(total_label_title)
        total_card_layout.addWidget(self.total_label)
        content_layout.addWidget(total_card)

        # Payment method
        method_label = QLabel("Mode de paiement")
        method_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        content_layout.addWidget(method_label)

        self.channel_select = QComboBox()
        for label, channel, _ in self.payment_service.payment_channels():
            self.channel_select.addItem(label, channel)
        self.channel_select.setMinimumHeight(52)
        content_layout.addWidget(self.channel_select)

        # Amount input
        amount_label = QLabel("Montant recu")
        amount_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        content_layout.addWidget(amount_label)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Entrez le montant donne par le client")
        self.amount_input.setMinimumHeight(52)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 14px 20px;
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)
        content_layout.addWidget(self.amount_input)

        # Reference input
        ref_label = QLabel("Reference transaction (optionnel)")
        ref_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        content_layout.addWidget(ref_label)

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Ex: numero de transaction mobile")
        self.reference_input.setMinimumHeight(48)
        content_layout.addWidget(self.reference_input)

        # Change display card
        self.change_card = QFrame()
        self.change_card.setStyleSheet("""
            QFrame {
                background: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 12px;
            }
        """)
        change_card_layout = QHBoxLayout(self.change_card)
        change_card_layout.setContentsMargins(20, 16, 20, 16)

        change_label_title = QLabel("Monnaie a rendre")
        change_label_title.setStyleSheet("color: #166534; font-size: 14px; font-weight: 500;")
        self.change_label = QLabel("0 FCFA")
        self.change_label.setStyleSheet("color: #15803D; font-size: 22px; font-weight: 800;")
        change_card_layout.addWidget(change_label_title)
        change_card_layout.addStretch()
        change_card_layout.addWidget(self.change_label)
        content_layout.addWidget(self.change_card)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()
        layout.addWidget(content, 1)

        # ── Footer ────────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 20, 28, 20)
        footer_layout.setSpacing(12)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setMinimumHeight(52)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 600;
                padding: 0 32px;
            }
            QPushButton:hover {
                background: #E2E8F0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("Confirmer le paiement")
        self.confirm_btn.setMinimumHeight(52)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                padding: 0 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        self.confirm_btn.clicked.connect(self._validate)

        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(self.confirm_btn, 1)
        layout.addWidget(footer)

        # Connections
        self.channel_select.currentIndexChanged.connect(self._payment_mode_changed)
        self.amount_input.textChanged.connect(self._recompute_change)

        self._payment_mode_changed()

    def set_preferred_channel(self, payment_channel: str) -> None:
        for idx in range(self.channel_select.count()):
            if self.channel_select.itemData(idx) == payment_channel:
                self.channel_select.setCurrentIndex(idx)
                break

    def set_channel(self, payment_channel: str) -> None:
        """Alias pour set_preferred_channel - compatibilite avec pos_screen"""
        self.set_preferred_channel(payment_channel)

    def get_amount_received(self) -> Decimal:
        """Retourne le montant recu par le client"""
        return self.amount_given

    def get_channel(self) -> str:
        """Retourne le canal de paiement selectionne"""
        return self.selected_channel

    def _payment_mode_changed(self) -> None:
        self.selected_channel = str(self.channel_select.currentData())
        self.selected_method = self.payment_service.resolve_payment_method(self.selected_channel)

        is_cash = self.payment_service.is_cash_payment(self.selected_channel)
        self.amount_input.setEnabled(is_cash)
        self.change_card.setVisible(is_cash)

        if not is_cash:
            self.amount_given = self.total
            self.change = Decimal("0")
            self.amount_input.setText(f"{int(self.total)}")
            self.status_label.setText("Confirmez la reception du paiement mobile / carte")
            self.status_label.setStyleSheet("color: #D97706; font-size: 13px; font-weight: 600;")
        else:
            self.amount_input.clear()
            self.status_label.setText("")
            self.amount_input.setFocus()

        self._recompute_change()

    def _recompute_change(self) -> None:
        try:
            self.amount_given = Decimal(self.amount_input.text().strip() or "0")
        except InvalidOperation:
            self.status_label.setText("Montant invalide")
            self.status_label.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 600;")
            return

        self.change = self.payment_service.calculate_change(self.amount_given, self.total)
        self.change_label.setText(f"{int(self.change):,} FCFA")

        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            if self.payment_service.is_cash_payment(self.selected_channel):
                self.status_label.setText("Montant suffisant")
                self.status_label.setStyleSheet("color: #16A34A; font-size: 13px; font-weight: 600;")
                self.change_card.setStyleSheet("""
                    QFrame {
                        background: #F0FDF4;
                        border: 1px solid #BBF7D0;
                        border-radius: 12px;
                    }
                """)
        else:
            self.status_label.setText("Montant insuffisant")
            self.status_label.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 600;")
            self.change_card.setStyleSheet("""
                QFrame {
                    background: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 12px;
                }
            """)
            self.change_label.setStyleSheet("color: #DC2626; font-size: 22px; font-weight: 800;")

    def _validate(self) -> None:
        self.transaction_reference = self.reference_input.text().strip()
        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            self.accept()
        else:
            self.status_label.setText("Montant insuffisant - impossible de valider")
            self.status_label.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 600;")
