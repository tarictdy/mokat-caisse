from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from services.payment_service import PaymentService


class PaymentDialog(QDialog):
    def __init__(self, total: Decimal, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.total = total
        self.payment_service = PaymentService()
        self.amount_given = Decimal("0")
        self.change = Decimal("0")

        self.setWindowTitle("Paiement")
        self.total_label = QLabel(f"TOTAL A PAYER : {int(total)} FCFA")
        self.amount_input = QLineEdit()
        self.change_label = QLabel("Monnaie à rendre : 0 FCFA")
        self.status_label = QLabel("")
        self.confirm_btn = QPushButton("Valider paiement")

        self.amount_input.textChanged.connect(self._recompute_change)
        self.confirm_btn.clicked.connect(self._validate)

        form = QFormLayout()
        form.addRow("Montant donné :", self.amount_input)

        layout = QVBoxLayout(self)
        layout.addWidget(self.total_label)
        layout.addLayout(form)
        layout.addWidget(self.change_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.confirm_btn)

    def _recompute_change(self) -> None:
        try:
            self.amount_given = Decimal(self.amount_input.text().strip() or "0")
        except InvalidOperation:
            self.status_label.setText("Montant invalide")
            return

        self.change = self.payment_service.calculate_change(self.amount_given, self.total)
        self.change_label.setText(f"Monnaie à rendre : {int(self.change)} FCFA")
        if self.payment_service.is_payment_sufficient(self.amount_given, self.total):
            self.status_label.setText("Paiement suffisant")
        else:
            self.status_label.setText("Montant insuffisant")

    def _validate(self) -> None:
        if self.payment_service.is_payment_sufficient(self.amount_given, self.total):
            self.accept()
        else:
            self.status_label.setText("Impossible de valider: montant insuffisant")
