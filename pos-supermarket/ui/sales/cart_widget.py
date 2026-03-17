from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.sale_service import CartLine


class CartWidget(QWidget):
    """Widget panier avec design moderne"""
    
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Produit", "Prix unit.", "Qte", "Total"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: none;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 14px 12px;
                border-bottom: 1px solid #F1F5F9;
                color: #1F2937;
            }
            QTableWidget::item:selected {
                background: #EFF6FF;
                color: #1D4ED8;
            }
            QTableWidget::item:alternate {
                background: #FAFAFA;
            }
            QHeaderView::section {
                background: #F8FAFC;
                color: #64748B;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 14px 12px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Set row height
        self.table.verticalHeader().setDefaultSectionSize(52)
        
        layout.addWidget(self.table)

        # Empty state
        self.empty_state = QFrame()
        self.empty_state.setStyleSheet("background: transparent;")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel("Panier")
        empty_icon.setStyleSheet("font-size: 32px; color: #CBD5E1;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_text = QLabel("Aucun article dans le panier")
        empty_text.setStyleSheet("font-size: 14px; color: #94A3B8; margin-top: 8px;")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_hint = QLabel("Scannez un produit pour commencer")
        empty_hint.setStyleSheet("font-size: 12px; color: #CBD5E1;")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addWidget(empty_hint)
        
        layout.addWidget(self.empty_state)
        self._update_empty_state(True)

    def _update_empty_state(self, is_empty: bool) -> None:
        self.table.setVisible(not is_empty)
        self.empty_state.setVisible(is_empty)

    def load_lines(self, lines: list[CartLine]) -> None:
        self._update_empty_state(len(lines) == 0)
        
        self.table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            # Product name with quantity badge
            name_item = QTableWidgetItem(line.product_name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            price_item = QTableWidgetItem(f"{int(line.unit_price):,}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            qty_item = QTableWidgetItem(str(line.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            
            total_item = QTableWidgetItem(f"{int(line.total_price):,}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, price_item)
            self.table.setItem(row, 2, qty_item)
            self.table.setItem(row, 3, total_item)

    def total(self, lines: list[CartLine]) -> Decimal:
        return sum((line.total_price for line in lines), Decimal("0.00"))
