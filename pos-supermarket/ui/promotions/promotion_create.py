from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PromotionCreateView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Créer promotion")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Workflow: produit -> type -> réduction -> dates -> activer"))
