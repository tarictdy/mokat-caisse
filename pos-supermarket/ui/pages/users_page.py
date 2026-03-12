from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class UsersPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("👥 Page utilisateurs (design prêt)"))
        layout.addStretch(1)
