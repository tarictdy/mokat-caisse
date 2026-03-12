from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class TopBar(QWidget):
    def __init__(self, username: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Rechercher produit")
        self.notifications_btn = QPushButton("🔔 Notifications")
        self.user_label = QLabel(f"👤 {username}")
        self.logout_btn = QPushButton("Déconnexion")

        layout.addWidget(self.search, 1)
        layout.addWidget(self.notifications_btn)
        layout.addWidget(self.user_label)
        layout.addWidget(self.logout_btn)
