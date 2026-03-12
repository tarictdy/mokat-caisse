from __future__ import annotations

from PyQt6.QtWidgets import QPushButton, QWidget


class IconButton(QPushButton):
    def __init__(self, text: str, icon_text: str = "", parent: QWidget | None = None) -> None:
        label = f"{icon_text} {text}".strip()
        super().__init__(label, parent)
        self.setMinimumHeight(40)
