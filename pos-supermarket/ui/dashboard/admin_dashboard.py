from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from models.user import User


class AdminDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.setWindowTitle("Dashboard Admin")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Bienvenue {user.prenom} ({user.role.value})"))
        layout.addWidget(QLabel("Modules: Produits, Promotions, Utilisateurs, Stock, Rapports, Paramètres"))
