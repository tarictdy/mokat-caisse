from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from models.user import User


class SupervisorDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.setWindowTitle("Dashboard Superviseur")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Superviseur: {user.prenom} {user.nom}"))
        layout.addWidget(QLabel("Accès: suivi ventes, stock, supervision caisse"))
