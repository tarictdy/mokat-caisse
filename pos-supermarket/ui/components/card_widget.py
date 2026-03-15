from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class CardWidget(QFrame):
    """Stat card: displays a title, a large value, and an optional subtitle."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        accent_color: str = "#2563EB",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(4)

        # Accent top bar
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: {accent_color}; border-radius: 2px;")
        layout.addWidget(bar)

        # Title
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B;"
            "letter-spacing: 0.7px; text-transform: uppercase; margin-top: 8px;"
        )
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)

        # Value
        self.value = QLabel(value)
        self.value.setStyleSheet(
            f"font-size: 28px; font-weight: 800; color: {accent_color}; margin-top: 4px;"
        )
        self.value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.value)

        # Subtitle
        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet("font-size: 12px; color: #94A3B8; margin-top: 2px;")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)

        layout.addStretch()
