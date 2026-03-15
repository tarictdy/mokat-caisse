from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from models.product import Product, ProductStatus
from models.promotion import Promotion, PromotionType
from models.stock_movement import StockMovement, StockMovementType
from models.user import User, UserRole
from repositories.product_repo import ProductRepository
from repositories.promotion_repo import PromotionRepository
from repositories.sale_repo import SaleRepository
from repositories.user_repo import UserRepository
from services.product_service import ProductService
from services.sale_service import SaleService
from services.user_service import UserService
from ui.sales.pos_screen import POSScreen


@dataclass
class DashboardStats:
    total_products: int
    low_stock_products: int
    active_promotions: int
    sales_today: Decimal


# ── Dialogs ────────────────────────────────────────────────────────────────────

class ProductCreateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter un produit")
        self.setModal(True)
        self.resize(540, 640)

        self.barcode_input = QLineEdit()
        self.reference_input = QLineEdit()
        self.name_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.description_input = QLineEdit()
        self.purchase_price_input = QLineEdit("0")
        self.sale_price_input = QLineEdit()
        self.tax_rate_input = QLineEdit("0")
        self.stock_input = QSpinBox(); self.stock_input.setRange(0, 1_000_000)
        self.stock_min_input = QSpinBox(); self.stock_min_input.setRange(0, 1_000_000)
        self.stock_max_input = QSpinBox(); self.stock_max_input.setRange(0, 1_000_000)
        self.unit_input = QComboBox(); self.unit_input.addItems(["piece", "kg", "litre", "paquet"])
        self.expiration_input = QDateEdit(); self.expiration_input.setCalendarPopup(True); self.expiration_input.setDate(QDate.currentDate())
        self.category_id_input = QSpinBox(); self.category_id_input.setRange(0, 999999)
        self.supplier_id_input = QSpinBox(); self.supplier_id_input.setRange(0, 999999)
        self.image_path_input = QLineEdit()
        self.promotion_eligible_check = QCheckBox("Eligible aux promotions")
        self.promotion_eligible_check.setChecked(True)

        form = QFormLayout(self)
        form.setSpacing(10)
        form.addRow("Nom du produit *", self.name_input)
        form.addRow("Code-barres *", self.barcode_input)
        form.addRow("Reference interne", self.reference_input)
        form.addRow("Categorie (ID)", self.category_id_input)
        form.addRow("Marque", self.brand_input)
        form.addRow("Description", self.description_input)
        form.addRow("Prix d'achat", self.purchase_price_input)
        form.addRow("Prix de vente *", self.sale_price_input)
        form.addRow("TVA (%)", self.tax_rate_input)
        form.addRow("Stock actuel", self.stock_input)
        form.addRow("Stock minimum", self.stock_min_input)
        form.addRow("Stock maximum", self.stock_max_input)
        form.addRow("Unite", self.unit_input)
        form.addRow("Date expiration", self.expiration_input)
        form.addRow("Fournisseur (ID)", self.supplier_id_input)
        form.addRow("Image (chemin)", self.image_path_input)
        form.addRow("", self.promotion_eligible_check)

        save_btn = QPushButton("Enregistrer le produit")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


class PromotionCreateDialog(QDialog):
    def __init__(self, products: list[Product], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Creer une promotion")
        self.setModal(True)
        self.resize(400, 260)

        self.product_box = QComboBox()
        for p in products:
            self.product_box.addItem(f"{p.name} ({p.barcode})", p.id)

        self.type_box = QComboBox()
        self.type_box.addItem("Pourcentage", PromotionType.PERCENTAGE)
        self.type_box.addItem("Montant fixe", PromotionType.FIXED)

        self.name_input = QLineEdit()
        self.value_input = QLineEdit()

        form = QFormLayout(self)
        form.setSpacing(10)
        form.addRow("Nom promotion", self.name_input)
        form.addRow("Produit", self.product_box)
        form.addRow("Type", self.type_box)
        form.addRow("Valeur", self.value_input)

        save_btn = QPushButton("Creer la promotion")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


class UserCreateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Creer un utilisateur")
        self.setModal(True)
        self.resize(400, 340)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit(); self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.code_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.role_box = QComboBox()
        self.role_box.addItem("Admin", UserRole.ADMIN)
        self.role_box.addItem("Superviseur", UserRole.SUPERVISOR)
        self.role_box.addItem("Caissier", UserRole.CASHIER)

        form = QFormLayout(self)
        form.setSpacing(10)
        form.addRow("Username", self.username_input)
        form.addRow("Mot de passe", self.password_input)
        form.addRow("Nom", self.nom_input)
        form.addRow("Prenom", self.prenom_input)
        form.addRow("Code employe", self.code_input)
        form.addRow("Telephone", self.phone_input)
        form.addRow("Role", self.role_box)

        save_btn = QPushButton("Creer l'utilisateur")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


# ── Main dashboard ─────────────────────────────────────────────────────────────

class AdminDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self._pos_windows: list[POSScreen] = []
        self.setWindowTitle("MOKAT MARKET — Administration")
        self.resize(1360, 840)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────
        sidebar_container = QWidget()
        sidebar_container.setObjectName("LoginRoot")
        sidebar_container.setFixedWidth(220)
        sidebar_v = QVBoxLayout(sidebar_container)
        sidebar_v.setContentsMargins(0, 0, 0, 0)
        sidebar_v.setSpacing(0)

        # Branding header
        brand_widget = QWidget()
        brand_widget.setStyleSheet("background: #0F172A; border: none;")
        brand_layout = QVBoxLayout(brand_widget)
        brand_layout.setContentsMargins(20, 22, 20, 16)
        brand_lbl = QLabel("MOKAT MARKET")
        brand_lbl.setStyleSheet(
            "color: #2563EB; font-size: 13px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )
        role_lbl = QLabel("Administration")
        role_lbl.setStyleSheet(
            "color: #475569; font-size: 11px; background: transparent; margin-top: 2px;"
        )
        brand_layout.addWidget(brand_lbl)
        brand_layout.addWidget(role_lbl)

        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            "color: #334155; font-size: 10px; font-weight: 700;"
            "letter-spacing: 1.2px; padding: 14px 20px 6px 20px;"
            "background: #0F172A; border: none;"
        )

        self.menu = QListWidget()
        self.menu.setObjectName("Sidebar")
        self.menu.setFixedWidth(220)
        self._populate_sidebar()

        # Bottom user info
        user_footer = QWidget()
        user_footer.setStyleSheet("background: #0F172A; border: none;")
        uf_layout = QHBoxLayout(user_footer)
        uf_layout.setContentsMargins(16, 14, 16, 20)
        uf_layout.setSpacing(10)
        avatar = QLabel(user.prenom[0].upper() if user.prenom else "A")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background: #1E40AF; color: #FFFFFF; border-radius: 17px;"
            "font-size: 13px; font-weight: 700;"
        )
        name_v = QVBoxLayout()
        name_v.setSpacing(0)
        name_lbl = QLabel(f"{user.prenom} {user.nom}")
        name_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600; background: transparent;")
        role_badge = QLabel("Administrateur")
        role_badge.setStyleSheet("color: #475569; font-size: 10px; background: transparent;")
        name_v.addWidget(name_lbl)
        name_v.addWidget(role_badge)
        uf_layout.addWidget(avatar)
        uf_layout.addLayout(name_v)
        uf_layout.addStretch()

        sidebar_v.addWidget(brand_widget)
        sidebar_v.addWidget(nav_label)
        sidebar_v.addWidget(self.menu, 1)
        sidebar_v.addWidget(user_footer)

        # ── Content area ─────────────────────────────────────
        content_container = QWidget()
        content_v = QVBoxLayout(content_container)
        content_v.setContentsMargins(0, 0, 0, 0)
        content_v.setSpacing(0)

        # Topbar
        topbar = self._build_topbar()
        content_v.addWidget(topbar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.products_page = self._build_products_page()
        self.promotions_page = self._build_placeholder_page("Promotions")
        self.users_page = self._build_placeholder_page("Utilisateurs")
        self.stock_page = self._build_stock_page()
        self.pos_page = self._build_pos_page()
        self.reports_page = self._build_placeholder_page("Rapports")
        self.settings_page = self._build_placeholder_page("Parametres")

        for page in [
            self.dashboard_page,
            self.products_page,
            self.promotions_page,
            self.users_page,
            self.stock_page,
            self.pos_page,
            self.reports_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        content_v.addWidget(self.stack, 1)

        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)

        root.addWidget(sidebar_container)
        root.addWidget(content_container, 1)

        self.refresh_dashboard()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _populate_sidebar(self) -> None:
        entries = [
            "  Dashboard",
            "  Produits",
            "  Promotions",
            "  Utilisateurs",
            "  Stock",
            "  Caisse",
            "  Rapports",
            "  Parametres",
        ]
        for label in entries:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.menu.addItem(item)

    # ── Topbar ────────────────────────────────────────────────────────────────

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self.topbar_search = QLineEdit()
        self.topbar_search.setObjectName("SearchInput")
        self.topbar_search.setPlaceholderText("Rechercher produit, code-barres...")
        self.topbar_search.setFixedWidth(300)
        self.topbar_search.setFixedHeight(34)
        self.topbar_search.returnPressed.connect(self._search_products)
        self.topbar_search.textChanged.connect(self._search_products)

        layout.addWidget(self.topbar_search)
        layout.addStretch()

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self.refresh_dashboard)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E2E8F0;")
        sep.setFixedHeight(28)

        user_lbl = QLabel(f"{self.user.prenom} {self.user.nom}")
        user_lbl.setStyleSheet("color: #374151; font-weight: 600; font-size: 13px;")

        layout.addWidget(refresh_btn)
        layout.addWidget(sep)
        layout.addWidget(user_lbl)
        return bar

    # ── Dashboard page ────────────────────────────────────────────────────────

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Page header
        header = QHBoxLayout()
        title = QLabel("Vue d'ensemble")
        title.setObjectName("PageTitle")
        sub = QLabel(f"Bienvenue, {self.user.prenom} {self.user.nom}")
        sub.setStyleSheet("color: #64748B; font-size: 13px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(sub)
        layout.addLayout(header)

        # Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.total_products_label = self._create_stat_card(cards_row, "Total produits", "#2563EB")
        self.low_stock_label = self._create_stat_card(cards_row, "Rupture / stock faible", "#D97706")
        self.active_promotions_label = self._create_stat_card(cards_row, "Promotions actives", "#16A34A")
        self.sales_today_label = self._create_stat_card(cards_row, "Ventes du jour (FCFA)", "#7C3AED")
        layout.addLayout(cards_row)

        # Quick actions row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Recherche produit: nom / code-barres / reference...")
        self.search_input.returnPressed.connect(self._search_products)
        self.search_input.textChanged.connect(self._search_products)
        add_product_btn = QPushButton("+ Produit")
        add_product_btn.clicked.connect(self._create_product)
        add_promo_btn = QPushButton("+ Promotion")
        add_promo_btn.clicked.connect(self._create_promotion)
        add_user_btn = QPushButton("+ Utilisateur")
        add_user_btn.clicked.connect(self._create_user)
        open_pos_btn = QPushButton("Ouvrir Caisse")
        open_pos_btn.setObjectName("SuccessButton")
        open_pos_btn.clicked.connect(self._open_pos_screen)

        actions_row.addWidget(self.search_input, 1)
        actions_row.addWidget(add_product_btn)
        actions_row.addWidget(add_promo_btn)
        actions_row.addWidget(add_user_btn)
        actions_row.addWidget(open_pos_btn)
        layout.addLayout(actions_row)

        # Search results table
        self.search_table = QTableWidget(0, 7)
        self.search_table.setHorizontalHeaderLabels(["ID", "Barcode", "Ref", "Nom", "Marque", "Prix", "Stock"])
        self.search_table.setAlternatingRowColors(True)
        self.search_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_table.verticalHeader().setVisible(False)
        layout.addWidget(self.search_table, 1)

        # Notifications + activity
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        self.notifications_box = QTextEdit(); self.notifications_box.setReadOnly(True); self.notifications_box.setMaximumHeight(160)
        self.activity_box = QTextEdit(); self.activity_box.setReadOnly(True); self.activity_box.setMaximumHeight(160)
        notif_group = QGroupBox("Alertes systeme")
        QVBoxLayout(notif_group).addWidget(self.notifications_box)
        activity_group = QGroupBox("Activite recente")
        QVBoxLayout(activity_group).addWidget(self.activity_box)
        bottom_row.addWidget(notif_group)
        bottom_row.addWidget(activity_group)
        layout.addLayout(bottom_row)

        return page

    def _create_stat_card(self, row: QHBoxLayout, title: str, color: str) -> QLabel:
        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumWidth(180)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(4)

        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px;")
        card_layout.addWidget(bar)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B;"
            "letter-spacing: 0.7px; text-transform: uppercase; margin-top: 8px;"
        )
        card_layout.addWidget(lbl_title)

        value = QLabel("0")
        value.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {color};")
        card_layout.addWidget(value)
        card_layout.addStretch()

        row.addWidget(card)
        return value

    # ── Products page ─────────────────────────────────────────────────────────

    def _build_products_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("Gestion des produits")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        actions = QHBoxLayout(); actions.setSpacing(10)
        self.products_search_input = QLineEdit()
        self.products_search_input.setObjectName("SearchInput")
        self.products_search_input.setPlaceholderText("Rechercher un produit...")
        self.products_search_input.textChanged.connect(self._refresh_products_table)
        btn_add = QPushButton("+ Ajouter"); btn_add.clicked.connect(self._create_product)
        btn_toggle = QPushButton("Activer / Desactiver"); btn_toggle.setObjectName("SecondaryButton"); btn_toggle.clicked.connect(self._toggle_selected_product_status)
        btn_delete = QPushButton("Supprimer"); btn_delete.setObjectName("DangerButton"); btn_delete.clicked.connect(self._delete_selected_product)
        actions.addWidget(self.products_search_input, 1)
        actions.addWidget(btn_add); actions.addWidget(btn_toggle); actions.addWidget(btn_delete)
        layout.addLayout(actions)

        self.products_table = QTableWidget(0, 9)
        self.products_table.setHorizontalHeaderLabels(["ID", "Barcode", "Ref", "Nom", "Marque", "Prix vente", "Stock", "Stock min", "Statut"])
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.verticalHeader().setVisible(False)
        layout.addWidget(self.products_table, 1)
        return page

    # ── Stock page ────────────────────────────────────────────────────────────

    def _build_stock_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("Gestion du stock")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        actions = QHBoxLayout(); actions.setSpacing(10)
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setObjectName("SearchInput")
        self.stock_search_input.setPlaceholderText("Rechercher un produit...")
        self.stock_search_input.textChanged.connect(self._refresh_stock_table)
        btn_entry = QPushButton("+ Entree stock"); btn_entry.setObjectName("SuccessButton"); btn_entry.clicked.connect(lambda: self._record_stock_movement(StockMovementType.ENTRY))
        btn_loss = QPushButton("Sortie / Perte"); btn_loss.setObjectName("DangerButton"); btn_loss.clicked.connect(lambda: self._record_stock_movement(StockMovementType.LOSS))
        btn_adjust = QPushButton("Ajustement"); btn_adjust.setObjectName("SecondaryButton"); btn_adjust.clicked.connect(lambda: self._record_stock_movement(StockMovementType.ADJUSTMENT))
        btn_restock = QPushButton("Renouveler"); btn_restock.clicked.connect(self._restock_selected_product)
        btn_exact = QPushButton("Inventaire manuel"); btn_exact.setObjectName("SecondaryButton"); btn_exact.clicked.connect(self._set_selected_stock)
        actions.addWidget(self.stock_search_input, 1)
        actions.addWidget(btn_entry); actions.addWidget(btn_loss); actions.addWidget(btn_adjust); actions.addWidget(btn_restock); actions.addWidget(btn_exact)
        layout.addLayout(actions)

        self.stock_table = QTableWidget(0, 9)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Barcode", "Nom", "Stock", "Min", "Max", "Unite", "Expiration", "Statut"])
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.verticalHeader().setVisible(False)
        layout.addWidget(self.stock_table, 1)

        group = QGroupBox("Historique des mouvements de stock")
        g = QVBoxLayout(group)
        self.stock_history_table = QTableWidget(0, 6)
        self.stock_history_table.setHorizontalHeaderLabels(["Date", "Produit", "Type", "Quantite", "Raison", "Utilisateur"])
        self.stock_history_table.setAlternatingRowColors(True)
        self.stock_history_table.verticalHeader().setVisible(False)
        g.addWidget(self.stock_history_table)
        layout.addWidget(group)
        return page

    # ── POS page ──────────────────────────────────────────────────────────────

    def _build_pos_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("Interface Caisse")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        card = QFrame(); card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        info = QLabel("Ouvrez l'ecran de caisse tactile pour scanner les produits, encaisser et imprimer les tickets.")
        info.setStyleSheet("color: #64748B; font-size: 13px;")
        info.setWordWrap(True)
        card_layout.addWidget(info)

        open_btn = QPushButton("Ouvrir l'interface de caisse")
        open_btn.setObjectName("SuccessButton")
        open_btn.setMinimumHeight(48)
        open_btn.clicked.connect(self._open_pos_screen)
        card_layout.addWidget(open_btn)

        layout.addWidget(card)
        layout.addStretch(1)
        return page

    # ── Placeholder page ──────────────────────────────────────────────────────

    def _build_placeholder_page(self, module_name: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        lbl = QLabel(module_name)
        lbl.setObjectName("PageTitle")
        layout.addWidget(lbl)
        sub = QLabel("Ce module est en cours d'implementation.")
        sub.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(sub)
        layout.addStretch()
        return page

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_menu_changed(self, row: int) -> None:
        if row < 0:
            return
        self.stack.setCurrentIndex(row)
        if row == 1:
            self._refresh_products_table()
        if row == 4:
            self._refresh_stock_table()
            self._refresh_stock_history()

    def _open_pos_screen(self) -> None:
        session = SessionLocal()
        service = SaleService(SaleRepository(session), ProductRepository(session))
        pos_window = POSScreen(service, self.user)
        pos_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        pos_window.destroyed.connect(lambda *_: session.close())
        pos_window.show()
        self._pos_windows.append(pos_window)

    def _load_stats(self) -> DashboardStats:
        with SessionLocal() as session:
            return DashboardStats(
                total_products=ProductRepository(session).count_all(),
                low_stock_products=ProductRepository(session).count_low_stock(),
                active_promotions=PromotionRepository(session).count_active(date.today()),
                sales_today=SaleRepository(session).total_sales_for_day(date.today()),
            )

    def _fill_search_results(self, products: list[Product]) -> None:
        self.search_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.search_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.search_table.setItem(row, 1, QTableWidgetItem(p.barcode))
            self.search_table.setItem(row, 2, QTableWidgetItem(p.internal_reference or "-"))
            self.search_table.setItem(row, 3, QTableWidgetItem(p.name))
            self.search_table.setItem(row, 4, QTableWidgetItem(p.brand or "-"))
            self.search_table.setItem(row, 5, QTableWidgetItem(str(p.sale_price)))
            self.search_table.setItem(row, 6, QTableWidgetItem(str(p.stock_quantity)))

    def _load_notifications(self) -> None:
        with SessionLocal() as session:
            repo = ProductRepository(session)
            low_stock = repo.count_low_stock()
            products = repo.list_all()

        notifications: list[str] = []
        if low_stock > 0:
            notifications.append(f"[!] {low_stock} produit(s) sous le stock minimum.")
        expired = [p for p in products if p.expiration_date and p.expiration_date <= date.today()]
        near_exp = [p for p in products if p.expiration_date and 0 <= (p.expiration_date - date.today()).days <= 7]
        if expired:
            notifications.append(f"[X] {len(expired)} produit(s) expire(s).")
        if near_exp:
            notifications.append(f"[i] {len(near_exp)} produit(s) expirent sous 7 jours.")
        if not notifications:
            notifications.append("[OK] Aucun incident critique detecte.")
        self.notifications_box.setPlainText("\n".join(notifications))

    def _load_recent_activity(self) -> None:
        entries: list[tuple[str, object]] = []
        with SessionLocal() as session:
            products = ProductRepository(session).latest_created(5)
            promotions = PromotionRepository(session).latest_created(5)
            users = UserRepository(session).latest_created(5)
            for p in products:
                entries.append((f"Produit ajoute: {p.name}", p.created_at))
            for promo in promotions:
                entries.append((f"Promotion creee: {promo.name}", promo.created_at))
            for u in users:
                entries.append((f"Utilisateur cree: {u.username}", u.created_at))

        entries.sort(key=lambda x: x[1], reverse=True)
        self.activity_box.setPlainText(
            "\n".join(msg for msg, _ in entries[:12]) or "Aucune activite recente."
        )

    def _search_products(self) -> None:
        query = self.search_input.text().strip()
        if hasattr(self, "topbar_search") and not query:
            query = self.topbar_search.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query, limit=50) if query else repo.list_all()[:20]
        self._fill_search_results(products)

    def _refresh_products_table(self) -> None:
        query = self.products_search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query, 200) if query else repo.list_all()

        self.products_table.setRowCount(len(products))
        for row, p in enumerate(products):
            for col, val in enumerate([
                p.id, p.barcode, p.internal_reference or "-", p.name,
                p.brand or "-", p.sale_price, p.stock_quantity, p.stock_min, p.status.value,
            ]):
                self.products_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _refresh_stock_table(self) -> None:
        query = self.stock_search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query, 250) if query else repo.list_all()

        self.stock_table.setRowCount(len(products))
        for row, p in enumerate(products):
            status = "RUPTURE" if p.stock_quantity <= 0 else ("FAIBLE" if p.stock_quantity <= p.stock_min else "NORMAL")
            expiration = p.expiration_date.isoformat() if p.expiration_date else "-"
            for col, val in enumerate([p.id, p.barcode, p.name, p.stock_quantity, p.stock_min, p.stock_max, p.unit, expiration, status]):
                self.stock_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _refresh_stock_history(self) -> None:
        with SessionLocal() as session:
            movements = list(
                session.query(StockMovement)
                .order_by(StockMovement.created_at.desc())
                .limit(50)
                .all()
            )
            products = {p.id: p.name for p in ProductRepository(session).list_all()}

        self.stock_history_table.setRowCount(len(movements))
        for row, m in enumerate(movements):
            date_str = m.created_at.strftime("%Y-%m-%d %H:%M")
            product_name = products.get(m.product_id, f"ID {m.product_id}")
            for col, val in enumerate([date_str, product_name, m.type.value, m.quantity, m.reason or "-", m.user_id or "-"]):
                self.stock_history_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _selected_product_id_from_table(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _create_product(self) -> None:
        dialog = ProductCreateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not dialog.name_input.text().strip() or not dialog.barcode_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Nom et code-barres sont obligatoires")
            return

        try:
            purchase_price = Decimal(dialog.purchase_price_input.text().strip() or "0")
            sale_price = Decimal(dialog.sale_price_input.text().strip())
            tax_rate = Decimal(dialog.tax_rate_input.text().strip() or "0")
        except InvalidOperation:
            QMessageBox.warning(self, "Erreur", "Prix/TVA invalides")
            return

        qd = dialog.expiration_input.date()
        expiration_date = date(qd.year(), qd.month(), qd.day())

        with SessionLocal() as session:
            service = ProductService(ProductRepository(session))
            try:
                service.create_product(
                    barcode=dialog.barcode_input.text().strip(),
                    internal_reference=dialog.reference_input.text().strip() or None,
                    name=dialog.name_input.text().strip(),
                    brand=dialog.brand_input.text().strip() or None,
                    description=dialog.description_input.text().strip() or None,
                    purchase_price=purchase_price,
                    sale_price=sale_price,
                    tax_rate=tax_rate,
                    stock_quantity=dialog.stock_input.value(),
                    stock_min=dialog.stock_min_input.value(),
                    stock_max=dialog.stock_max_input.value(),
                    unit=dialog.unit_input.currentText(),
                    expiration_date=expiration_date,
                    category_id=dialog.category_id_input.value() or None,
                    supplier_id=dialog.supplier_id_input.value() or None,
                    image_path=dialog.image_path_input.text().strip() or None,
                    promotion_eligible=dialog.promotion_eligible_check.isChecked(),
                )
                session.commit()
            except ValueError as exc:
                session.rollback()
                QMessageBox.warning(self, "Erreur", str(exc))
                return
        self.refresh_dashboard()

    def _create_promotion(self) -> None:
        with SessionLocal() as session:
            products = ProductRepository(session).list_all()

        if not products:
            QMessageBox.information(self, "Information", "Ajoutez d'abord un produit.")
            return

        dialog = PromotionCreateDialog(products, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            discount_value = Decimal(dialog.value_input.text().strip())
        except InvalidOperation:
            QMessageBox.warning(self, "Erreur", "Valeur de promotion invalide")
            return

        promo_type: PromotionType = dialog.type_box.currentData()
        with SessionLocal() as session:
            promo = Promotion(
                name=dialog.name_input.text().strip() or "Promo",
                product_id=int(dialog.product_box.currentData()),
                type=promo_type,
                percentage_discount=discount_value if promo_type == PromotionType.PERCENTAGE else None,
                fixed_discount=discount_value if promo_type == PromotionType.FIXED else None,
                start_date=date.today(),
                end_date=date.today(),
                active=True,
            )
            PromotionRepository(session).add(promo)
            session.commit()
        self.refresh_dashboard()

    def _create_user(self) -> None:
        dialog = UserCreateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        with SessionLocal() as session:
            service = UserService(UserRepository(session))
            try:
                service.create_user(
                    username=dialog.username_input.text().strip(),
                    password=dialog.password_input.text(),
                    role=dialog.role_box.currentData(),
                    nom=dialog.nom_input.text().strip() or "Nom",
                    prenom=dialog.prenom_input.text().strip() or "Prenom",
                    employee_code=dialog.code_input.text().strip() or f"EMP{date.today().strftime('%Y%m%d')}",
                    telephone=dialog.phone_input.text().strip() or None,
                )
                session.commit()
            except ValueError as exc:
                session.rollback()
                QMessageBox.warning(self, "Erreur", str(exc))
                return
        self.refresh_dashboard()

    def _delete_selected_product(self) -> None:
        product_id = self._selected_product_id_from_table(self.products_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Selectionnez un produit.")
            return
        if QMessageBox.question(self, "Confirmation", "Supprimer ce produit ?") != QMessageBox.StandardButton.Yes:
            return
        with SessionLocal() as session:
            if not ProductRepository(session).delete(product_id):
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            session.commit()
        self.refresh_dashboard()

    def _toggle_selected_product_status(self) -> None:
        product_id = self._selected_product_id_from_table(self.products_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Selectionnez un produit.")
            return
        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.get_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            new_status = ProductStatus.INACTIVE if product.status == ProductStatus.ACTIVE else ProductStatus.ACTIVE
            repo.set_status(product_id, new_status)
            session.commit()
        self.refresh_dashboard()

    def _record_stock_movement(self, movement_type: StockMovementType) -> None:
        product_id = self._selected_product_id_from_table(self.stock_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Selectionnez un produit dans le tableau stock.")
            return
        qty, ok = QInputDialog.getInt(self, "Mouvement stock", "Quantite", 1, 1, 1_000_000)
        if not ok:
            return
        reason, ok = QInputDialog.getText(self, "Mouvement stock", "Raison")
        if not ok:
            return
        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.get_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            if movement_type == StockMovementType.ENTRY:
                product.stock_quantity += qty
            elif movement_type in (StockMovementType.LOSS, StockMovementType.ADJUSTMENT):
                product.stock_quantity = max(0, product.stock_quantity - qty)
            movement = StockMovement(
                product_id=product_id, type=movement_type, quantity=qty,
                reason=reason or movement_type.value, user_id=self.user.id,
            )
            session.add(movement)
            session.commit()
        self.refresh_dashboard()

    def _restock_selected_product(self) -> None:
        product_id = self._selected_product_id_from_table(self.stock_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Selectionnez un produit.")
            return
        qty, ok = QInputDialog.getInt(self, "Renouvellement", "Quantite a ajouter", 1, 1, 1_000_000)
        if not ok:
            return
        with SessionLocal() as session:
            repo = ProductRepository(session)
            if not repo.restock(product_id, qty):
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            session.add(StockMovement(product_id=product_id, type=StockMovementType.ENTRY, quantity=qty, reason="restock", user_id=self.user.id))
            session.commit()
        self.refresh_dashboard()

    def _set_selected_stock(self) -> None:
        product_id = self._selected_product_id_from_table(self.stock_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Selectionnez un produit.")
            return
        qty, ok = QInputDialog.getInt(self, "Inventaire manuel", "Stock reel", 0, 0, 1_000_000)
        if not ok:
            return
        with SessionLocal() as session:
            repo = ProductRepository(session)
            product = repo.get_by_id(product_id)
            if not product:
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            old_qty = product.stock_quantity
            if not repo.update_stock(product_id, qty):
                QMessageBox.warning(self, "Erreur", "Mise a jour impossible")
                return
            diff = abs(qty - old_qty)
            session.add(StockMovement(product_id=product_id, type=StockMovementType.ADJUSTMENT, quantity=diff, reason="inventaire manuel", user_id=self.user.id))
            session.commit()
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        stats = self._load_stats()
        self.total_products_label.setText(str(stats.total_products))
        self.low_stock_label.setText(str(stats.low_stock_products))
        self.active_promotions_label.setText(str(stats.active_promotions))
        self.sales_today_label.setText(f"{int(stats.sales_today):,}")
        self._search_products()
        self._load_notifications()
        self._load_recent_activity()
        self._refresh_products_table()
        self._refresh_stock_table()
        self._refresh_stock_history()
