from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProductListView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Produits")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Tableau: Barcode | Nom | Prix | Stock | Catégorie"))
