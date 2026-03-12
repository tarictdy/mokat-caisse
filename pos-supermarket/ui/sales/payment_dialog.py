from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
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

        self.setWindowTitle("Paiement")
        self.total_label = QLabel(f"TOTAL A PAYER : {int(total)} FCFA")

        self.channel_select = QComboBox()
        for label, channel, _ in self.payment_service.payment_channels():
            self.channel_select.addItem(label, channel)

        self.amount_input = QLineEdit()
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Référence transaction (optionnel)")

        self.change_label = QLabel("Monnaie à rendre : 0 FCFA")
        self.status_label = QLabel("")
        self.confirm_btn = QPushButton("Valider paiement")

        self.channel_select.currentIndexChanged.connect(self._payment_mode_changed)
        self.amount_input.textChanged.connect(self._recompute_change)
        self.confirm_btn.clicked.connect(self._validate)

        form = QFormLayout()
        form.addRow("Mode de paiement :", self.channel_select)
        form.addRow("Montant donné :", self.amount_input)
        form.addRow("Référence :", self.reference_input)

        layout = QVBoxLayout(self)
        layout.addWidget(self.total_label)
        layout.addLayout(form)
        layout.addWidget(self.change_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.confirm_btn)

        self._payment_mode_changed()

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
            self.status_label.setText("Confirmez la réception du paiement mobile/carte")
        else:
            self.amount_input.clear()
            self.status_label.setText("")

        self._recompute_change()

    def _recompute_change(self) -> None:
        try:
            self.amount_given = Decimal(self.amount_input.text().strip() or "0")
        except InvalidOperation:
            self.status_label.setText("Montant invalide")
            return

        self.change = self.payment_service.calculate_change(self.amount_given, self.total)
        self.change_label.setText(f"Monnaie à rendre : {int(self.change)} FCFA")

        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            if self.payment_service.is_cash_payment(self.selected_channel):
                self.status_label.setText("Paiement suffisant")
        else:
            self.status_label.setText("Montant insuffisant")

    def _validate(self) -> None:
        self.transaction_reference = self.reference_input.text().strip()
        if self.payment_service.is_payment_sufficient(self.amount_given, self.total, self.selected_channel):
            self.accept()
        else:
            self.status_label.setText("Impossible de valider: montant insuffisant")
