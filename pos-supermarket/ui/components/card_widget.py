from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class CardWidget(QFrame):
    def __init__(self, title: str, value: str = "0", subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.value = QLabel(value)
        self.value.setStyleSheet("font-size:24px;font-weight:700;")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet("color:#64748b;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.subtitle)
