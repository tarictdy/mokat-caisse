from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


_SIDEBAR_ENTRIES = [
    ("  Dashboard",     "dashboard"),
    ("  Produits",      "products"),
    ("  Promotions",    "promotions"),
    ("  Utilisateurs",  "users"),
    ("  Stock",         "stock"),
    ("  Caisse",        "caisse"),
    ("  Rapports",      "reports"),
    ("  Parametres",    "settings"),
]

# Unicode block icons (no emoji, clean monospace look)
_ICONS = {
    "dashboard":    "\u25A0",   # filled square
    "products":     "\u25A6",   # square with diagonal crosshatch
    "promotions":   "\u2605",   # star
    "users":        "\u25CF",   # circle
    "stock":        "\u25A3",   # square
    "caisse":       "\u25B6",   # triangle right
    "reports":      "\u2261",   # triple bar
    "settings":     "\u2699",   # gear (unicode)
}


class Sidebar(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        # Header label
        self._header = QLabel("NAVIGATION")
        self._header.setStyleSheet(
            "color: #334155; font-size: 10px; font-weight: 700;"
            "letter-spacing: 1.2px; padding: 20px 20px 8px 20px;"
            "background: #0F172A; border: none;"
        )

        for label, key in _SIDEBAR_ENTRIES:
            icon = _ICONS.get(key, "\u25AA")
            item = QListWidgetItem(f" {icon}  {label.strip()}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.addItem(item)

    def header_widget(self) -> QLabel:
        """Return the header label to embed above the sidebar."""
        return self._header
