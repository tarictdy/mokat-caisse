from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ui.components.modern_table import ModernTable


class ProductsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        table = ModernTable(0, 5)
        table.setHorizontalHeaderLabels(["Code barre", "Nom", "Prix", "Stock", "Catégorie"])
        layout.addWidget(table)
