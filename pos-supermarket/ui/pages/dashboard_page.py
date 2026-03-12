from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from ui.components.card_widget import CardWidget


class DashboardPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.addWidget(CardWidget("📦 Total produits", "0", "Inventaire actuel"), 0, 0)
        grid.addWidget(CardWidget("⚠️ Stock faible", "0", "Produits à réapprovisionner"), 0, 1)
        grid.addWidget(CardWidget("💰 Ventes du jour", "0 FCFA", "Chiffre journalier"), 0, 2)
        layout.addLayout(grid)
        layout.addStretch(1)
