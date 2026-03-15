from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class TopBar(QWidget):
    def __init__(self, username: str, role: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # Search input
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Rechercher un produit, code-barres...")
        self.search.setFixedWidth(280)
        self.search.setFixedHeight(34)

        # Spacer
        layout.addWidget(self.search)
        layout.addStretch()

        # Notifications button
        self.notifications_btn = QPushButton("Notifications")
        self.notifications_btn.setObjectName("SecondaryButton")
        self.notifications_btn.setFixedHeight(34)
        self.notifications_btn.setFixedWidth(120)

        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E2E8F0;")
        sep.setFixedHeight(28)

        # User badge
        user_badge = QWidget()
        user_badge.setStyleSheet(
            "background: #EFF6FF; border-radius: 18px; padding: 0 10px;"
        )
        badge_layout = QHBoxLayout(user_badge)
        badge_layout.setContentsMargins(10, 4, 10, 4)
        badge_layout.setSpacing(6)

        avatar = QLabel("A" if not username else username[0].upper())
        avatar.setStyleSheet(
            "background: #2563EB; color: #FFFFFF; border-radius: 12px;"
            "min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px;"
            "font-size: 11px; font-weight: 700; qproperty-alignment: AlignCenter;"
        )
        self.user_label = QLabel(username)
        self.user_label.setStyleSheet("color: #1E40AF; font-weight: 600; font-size: 13px;")

        role_lbl = QLabel(role)
        role_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; padding-left: 4px;"
        )

        badge_layout.addWidget(avatar)
        badge_layout.addWidget(self.user_label)
        if role:
            badge_layout.addWidget(role_lbl)

        # Logout button
        self.logout_btn = QPushButton("Deconnexion")
        self.logout_btn.setObjectName("SecondaryButton")
        self.logout_btn.setFixedHeight(34)

        layout.addWidget(self.notifications_btn)
        layout.addWidget(sep)
        layout.addWidget(user_badge)
        layout.addWidget(self.logout_btn)
