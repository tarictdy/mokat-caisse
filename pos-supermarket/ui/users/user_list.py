from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class UserListView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Utilisateurs")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Liste utilisateurs par rôle"))
