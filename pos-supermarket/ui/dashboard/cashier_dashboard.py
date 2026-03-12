from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

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
        self.setWindowTitle("Caisse")
        self.resize(720, 420)

        layout = QVBoxLayout(self)
        title = QLabel("Interface Caissier")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel(f"👤 Caissier: {user.prenom} {user.nom}"))
        card_layout.addWidget(QLabel("Accès rapide: scan produit, paiement, reçu et impression ticket."))

        self.open_pos_btn = QPushButton("🛒 Ouvrir l'interface de caisse")
        self.open_pos_btn.setMinimumHeight(48)
        self.open_pos_btn.clicked.connect(self._open_pos_screen)
        card_layout.addWidget(self.open_pos_btn)

        layout.addWidget(card)
        layout.addStretch(1)

    def _open_pos_screen(self) -> None:
        session = SessionLocal()
        service = SaleService(SaleRepository(session), ProductRepository(session))
        pos_window = POSScreen(service, self.user)
        pos_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        pos_window.destroyed.connect(lambda *_: session.close())
        pos_window.show()
        self._pos_windows.append(pos_window)
