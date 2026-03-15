from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from models.sale import PaymentMethod
from services.payment_service import PaymentService


class PaymentDialog(QDialog):
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
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────
        header_lbl = QLabel("Encaissement")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(header_lbl)

        # Total display
        total_frame = QFrame()
        total_frame.setObjectName("Card")
        total_frame.setStyleSheet(
            "QFrame#Card { background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 16px; }"
        )
        total_v = QVBoxLayout(total_frame)
        total_v.setContentsMargins(16, 14, 16, 14)
        total_v.setSpacing(2)
        total_title = QLabel("TOTAL A PAYER")
        total_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3B82F6; letter-spacing: 0.8px;")
        self.total_label = QLabel(f"{int(total):,} FCFA")
        self.total_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #1E3A8A;")
        total_v.addWidget(total_title)
        total_v.addWidget(self.total_label)
        layout.addWidget(total_frame)

        # Separator
        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background: #E2E8F0;")
        layout.addWidget(sep)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(
            __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignRight
        )

        self.channel_select = QComboBox()
        for label, channel, _ in self.payment_service.payment_channels():
            self.channel_select.addItem(label, channel)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Montant donne par le client")
        self.amount_input.setMinimumHeight(40)

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Reference transaction (optionnel)")
        self.reference_input.setMinimumHeight(40)

        form.addRow("Mode de paiement :", self.channel_select)
        form.addRow("Montant donne :", self.amount_input)
        form.addRow("Reference :", self.reference_input)
        layout.addLayout(form)

        # Change display
        self.change_label = QLabel("Monnaie a rendre : 0 FCFA")
        self.change_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #16A34A;")
        layout.addWidget(self.change_label)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Confirm button
        self.confirm_btn = QPushButton("Valider le paiement")
        self.confirm_btn.setObjectName("SuccessButton")
        self.confirm_btn.setMinimumHeight(48)
        layout.addWidget(self.confirm_btn)

        # Connections
        self.channel_select.currentIndexChanged.connect(self._payment_mode_changed)
        self.amount_input.textChanged.connect(self._recompute_change)
        self.confirm_btn.clicked.connect(self._validate)

        self._payment_mode_changed()

    def set_preferred_channel(self, payment_channel: str) -> None:
        for idx in range(self.channel_select.count()):
            if self.channel_select.itemData(idx) == payment_channel:
                self.channel_select.setCurrentIndex(idx)
                break

    def _payment_mode_changed(self) -> None:
        self.selected_channel = str(self.channel_select.currentData())
        self.selected_method = self.payment_service.resolve_payment_method(self.selected_channel)

        is_cash = self.payment_service.is_cash_payment(self.selected_channel)
        self.amount_input.setEnabled(is_cash)
        self.change_label.setVisible(is_cash)

        if not is_cash:
            self.amount_given = self.total
            self.change = Decimal("0")
            self.amount_input.setText(f"{int(self.total)}")
            self.status_label.setText("Confirmez la reception du paiement mobile / carte")
            self.status_label.setObjectName("StatusWarning")
        else:
            self.amount_input.clear()
            self.status_label.setText("")
            self.status_label.setObjectName("")

        self._recompute_change()

    def _recompute_change(self) -> None:
        try:
            self.amount_given = Decimal(self.amount_input.text().strip() or "0")
        except InvalidOperation:
            self.status_label.setText("Montant invalide")
            return

        self.change = self.payment_service.calculate_change(self.amount_given, self.total)
        self.change_label.setText(f"Monnaie a rendre : {int(self.change):,} FCFA")

        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            if self.payment_service.is_cash_payment(self.selected_channel):
                self.status_label.setText("Montant suffisant")
                self.status_label.setStyleSheet("color: #16A34A; font-weight: 600;")
        else:
            self.status_label.setText("Montant insuffisant")
            self.status_label.setStyleSheet("color: #DC2626; font-weight: 600;")

    def _validate(self) -> None:
        self.transaction_reference = self.reference_input.text().strip()
        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            self.accept()
        else:
            self.status_label.setText("Impossible de valider : montant insuffisant")
            self.status_label.setStyleSheet("color: #DC2626; font-weight: 600;")
