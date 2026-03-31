from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models.user import User


class SupervisorDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.setWindowTitle("MOKAT MARKET — Superviseur")
        self.resize(1100, 700)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar_container = QWidget()
        self.sidebar_container.setObjectName("LoginRoot")
        self.sidebar_container.setFixedWidth(220)
        sidebar_v = QVBoxLayout(self.sidebar_container)
        sidebar_v.setContentsMargins(0, 0, 0, 0)
        sidebar_v.setSpacing(0)

        brand_widget = QWidget()
        brand_widget.setStyleSheet("background: #0F172A; border: none;")
        bw_layout = QVBoxLayout(brand_widget)
        bw_layout.setContentsMargins(20, 22, 20, 16)
        brand_lbl = QLabel("MOKAT MARKET")
        brand_lbl.setStyleSheet(
            "color: #2563EB; font-size: 13px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )
        role_badge = QLabel("Supervision")
        role_badge.setStyleSheet(
            "color: #475569; font-size: 11px; background: transparent; margin-top: 2px;"
        )
        bw_layout.addWidget(brand_lbl)
        bw_layout.addWidget(role_badge)

        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            "color: #334155; font-size: 10px; font-weight: 700;"
            "letter-spacing: 1.2px; padding: 14px 20px 6px 20px;"
            "background: #0F172A; border: none;"
        )

        self.menu = QListWidget()
        self.menu.setObjectName("Sidebar")
        self.menu.setFixedWidth(220)
        for label in ["  Tableau de bord", "  Suivi ventes", "  Stock"]:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.menu.addItem(item)

        user_footer = QWidget()
        user_footer.setStyleSheet("background: #0F172A; border: none;")
        uf_layout = QHBoxLayout(user_footer)
        uf_layout.setContentsMargins(16, 14, 16, 20)
        uf_layout.setSpacing(10)
        avatar = QLabel(user.prenom[0].upper() if user.prenom else "S")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background: #1E40AF; color: #FFFFFF; border-radius: 17px;"
            "font-size: 13px; font-weight: 700;"
        )
        name_v = QVBoxLayout()
        name_v.setSpacing(0)
        name_lbl = QLabel(f"{user.prenom} {user.nom}")
        name_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600; background: transparent;")
        rlbl = QLabel("Superviseur")
        rlbl.setStyleSheet("color: #475569; font-size: 10px; background: transparent;")
        name_v.addWidget(name_lbl)
        name_v.addWidget(rlbl)
        uf_layout.addWidget(avatar)
        uf_layout.addLayout(name_v)
        uf_layout.addStretch()

        sidebar_v.addWidget(brand_widget)
        sidebar_v.addWidget(nav_label)
        sidebar_v.addWidget(self.menu, 1)
        sidebar_v.addWidget(user_footer)

        # ── Content ───────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet("background: #F8FAFC;")
        content_v = QVBoxLayout(content)
        content_v.setContentsMargins(28, 28, 28, 28)
        content_v.setSpacing(16)

        title = QLabel("Tableau de bord superviseur")
        title.setObjectName("PageTitle")
        content_v.addWidget(title)

        info = QLabel("Acces : suivi ventes, stock, supervision caisse.")
        info.setStyleSheet("color: #64748B; font-size: 13px;")
        content_v.addWidget(info)
        content_v.addStretch()

        root.addWidget(self.sidebar_container)
        root.addWidget(content, 1)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.sidebar_container.setFixedWidth(160 if self.width() < 980 else 220)
