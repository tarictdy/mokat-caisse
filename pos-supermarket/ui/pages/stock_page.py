from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ui.components.modern_table import ModernTable


class StockPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        table = ModernTable(0, 4)
        table.setHorizontalHeaderLabels(["Produit", "Stock actuel", "Stock min", "Statut"])
        layout.addWidget(table)
