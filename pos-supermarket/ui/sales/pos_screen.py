from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class POSScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Point de vente")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Zone scan, panier, total, paiement"))
