from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProductEditView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Modifier produit")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Formulaire d'édition produit"))
