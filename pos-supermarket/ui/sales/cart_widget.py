from __future__ import annotations

from decimal import Decimal

from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from services.sale_service import CartLine


class CartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nom", "Prix", "Qté", "Total"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

    def load_lines(self, lines: list[CartLine]) -> None:
        self.table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            self.table.setItem(row, 0, QTableWidgetItem(line.product_name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{int(line.unit_price)}"))
            self.table.setItem(row, 2, QTableWidgetItem(str(line.quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{int(line.total_price)}"))

    def total(self, lines: list[CartLine]) -> Decimal:
        return sum((line.total_price for line in lines), Decimal("0.00"))
