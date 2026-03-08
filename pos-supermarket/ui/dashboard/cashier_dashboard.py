from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from models.user import User


class CashierDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.setWindowTitle("Caisse")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Caissier: {user.prenom} {user.nom}"))
        layout.addWidget(QLabel("Accès rapide: POS, paiement, impression ticket"))
