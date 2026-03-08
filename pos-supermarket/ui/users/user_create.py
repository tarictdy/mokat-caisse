from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class UserCreateView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Créer utilisateur")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Formulaire: username, password, nom, prenom, code, téléphone, rôle"))
