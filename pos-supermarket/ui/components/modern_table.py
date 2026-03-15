from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView, QTableWidget, QWidget


class ModernTable(QTableWidget):
    """Table with striped rows, no vertical header, and stretched columns."""

    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
