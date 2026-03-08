from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TicketPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Aperçu ticket")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Aperçu impression ticket de caisse"))
