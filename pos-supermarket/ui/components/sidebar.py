from __future__ import annotations

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QStyle, QWidget


class Sidebar(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(240)
        style = self.style()
        entries = [
            ("🏠 Dashboard", QStyle.StandardPixmap.SP_ComputerIcon),
            ("📦 Produits", QStyle.StandardPixmap.SP_FileDialogContentsView),
            ("📊 Stock", QStyle.StandardPixmap.SP_DriveHDIcon),
            ("🎯 Promotions", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("👥 Utilisateurs", QStyle.StandardPixmap.SP_DirHomeIcon),
            ("🛒 Caisse", QStyle.StandardPixmap.SP_ArrowForward),
            ("📈 Rapports", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("⚙️ Paramètres", QStyle.StandardPixmap.SP_FileDialogInfoView),
        ]
        for label, icon_key in entries:
            self.addItem(QListWidgetItem(style.standardIcon(icon_key), label))
