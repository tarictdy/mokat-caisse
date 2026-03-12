from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from ui.components.sidebar import Sidebar
from ui.components.topbar import TopBar
from ui.pages.dashboard_page import DashboardPage
from ui.pages.pos_page import POSPage
from ui.pages.products_page import ProductsPage
from ui.pages.promotions_page import PromotionsPage
from ui.pages.stock_page import StockPage
from ui.pages.users_page import UsersPage


class MainWindow(QWidget):
    def __init__(self, username: str) -> None:
        super().__init__()
        self.setWindowTitle("MokatShop POS - Interface Moderne")
        self.resize(1280, 820)

        root = QHBoxLayout(self)
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        self.topbar = TopBar(username)
        right.addWidget(self.topbar)

        self.stack = QStackedWidget()
        for page in [DashboardPage(), ProductsPage(), StockPage(), PromotionsPage(), UsersPage(), POSPage()]:
            self.stack.addWidget(page)
        right.addWidget(self.stack, 1)

        root.addLayout(right, 1)
        self.sidebar.currentRowChanged.connect(self._on_menu_changed)
        self.sidebar.setCurrentRow(0)

    def _on_menu_changed(self, row: int) -> None:
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)
