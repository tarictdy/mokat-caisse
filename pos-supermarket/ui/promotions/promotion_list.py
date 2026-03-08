from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PromotionListView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Promotions")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Liste des promotions actives/inactives"))
