from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProductAddView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ajouter produit")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Formulaire d'ajout produit"))
