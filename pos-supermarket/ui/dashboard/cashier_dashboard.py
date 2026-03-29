from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from models.user import User
from repositories.product_repo import ProductRepository
from repositories.sale_repo import SaleRepository
from services.sale_service import SaleService
from ui.sales.pos_screen import POSScreen


class CashierDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self._pos_windows: list[POSScreen] = []
        self.setWindowTitle("MOKAT MARKET — Caisse")
        self.setMinimumSize(640, 420)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left branding strip ───────────────────────────────
        self.left_panel = QWidget()
        self.left_panel.setObjectName("LoginRoot")
        self.left_panel.setFixedWidth(220)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(28, 32, 28, 28)
        left_layout.setSpacing(0)

        brand = QLabel("MOKAT MARKET")
        brand.setStyleSheet(
            "color: #2563EB; font-size: 15px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )
        module_lbl = QLabel("Interface Caissier")
        module_lbl.setStyleSheet(
            "color: #475569; font-size: 12px; background: transparent; margin-top: 4px;"
        )

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #1E293B; margin: 20px 0;")

        # Avatar + name
        avatar = QLabel(user.prenom[0].upper() if user.prenom else "C")
        avatar.setFixedSize(48, 48)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background: #1E40AF; color: #FFFFFF; border-radius: 24px;"
            "font-size: 20px; font-weight: 700;"
        )
        name_lbl = QLabel(f"{user.prenom} {user.nom}")
        name_lbl.setStyleSheet("color: #E2E8F0; font-size: 14px; font-weight: 600; background: transparent; margin-top: 10px;")
        role_lbl = QLabel("Caissier")
        role_lbl.setStyleSheet("color: #64748B; font-size: 12px; background: transparent;")

        left_layout.addStretch()
        left_layout.addWidget(brand)
        left_layout.addWidget(module_lbl)
        left_layout.addWidget(div)
        left_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(name_lbl)
        left_layout.addWidget(role_lbl)
        left_layout.addStretch()

        # ── Right content panel ───────────────────────────────
        right = QWidget()
        right.setStyleSheet("background: #F8FAFC;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumWidth(340)
        card.setMaximumWidth(400)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(16)

        card_title = QLabel("Caisse")
        card_title.setObjectName("PageTitle")
        card_layout.addWidget(card_title)

        desc = QLabel(
            "Acces rapide: scannez les produits, encaissez et imprimez les tickets."
        )
        desc.setStyleSheet("color: #64748B; font-size: 13px;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0;")
        card_layout.addWidget(sep)

        self.open_pos_btn = QPushButton("Ouvrir l'interface de caisse")
        self.open_pos_btn.setObjectName("SuccessButton")
        self.open_pos_btn.setMinimumHeight(48)
        self.open_pos_btn.clicked.connect(self._open_pos_screen)
        card_layout.addWidget(self.open_pos_btn)

        right_layout.addStretch()
        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch()

        root.addWidget(self.left_panel)
        root.addWidget(right, 1)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.left_panel.setFixedWidth(160 if self.width() < 900 else 220)

    def _open_pos_screen(self) -> None:
        session = SessionLocal()
        service = SaleService(SaleRepository(session), ProductRepository(session))
        pos_window = POSScreen(service, self.user)
        pos_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        pos_window.destroyed.connect(lambda *_: session.close())
        pos_window.show()
        self._pos_windows.append(pos_window)
