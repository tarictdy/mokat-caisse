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
    QScrollArea,
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


# ══════════════════════════════════════════════════════════════════════════════
# DIALOGS - Formulaires avec scroll
# ══════════════════════════════════════════════════════════════════════════════

class ProductCreateDialog(QDialog):
    """Dialogue creation produit avec scroll pour tous les champs"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouveau produit")
        self.setModal(True)
        self.setMinimumSize(560, 680)
        self.setStyleSheet("""
            QDialog {
                background: #F8FAFC;
            }
            QLabel {
                color: #374151;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit, QSpinBox, QComboBox, QDateEdit {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: #1F2937;
                min-height: 20px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #2563EB;
                outline: none;
            }
            QCheckBox {
                color: #374151;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #CBD5E1;
            }
            QCheckBox::indicator:checked {
                background: #2563EB;
                border-color: #2563EB;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 24, 28, 20)
        title = QLabel("Ajouter un nouveau produit")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        subtitle = QLabel("Remplissez les informations du produit")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 400;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F8FAFC; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_container = QWidget()
        form_container.setStyleSheet("background: #F8FAFC;")
        form = QVBoxLayout(form_container)
        form.setContentsMargins(28, 24, 28, 24)
        form.setSpacing(20)

        # === Section: Informations de base ===
        section1 = self._create_section("Informations de base")
        grid1 = QGridLayout()
        grid1.setSpacing(16)
        grid1.setColumnStretch(0, 1)
        grid1.setColumnStretch(1, 1)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Lait concentre sucre")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Ex: 6001234567890")
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Ex: REF-001")
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Ex: Nestle")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description du produit...")

        grid1.addWidget(self._field("Nom du produit *"), 0, 0)
        grid1.addWidget(self.name_input, 1, 0)
        grid1.addWidget(self._field("Code-barres *"), 0, 1)
        grid1.addWidget(self.barcode_input, 1, 1)
        grid1.addWidget(self._field("Reference interne"), 2, 0)
        grid1.addWidget(self.reference_input, 3, 0)
        grid1.addWidget(self._field("Marque"), 2, 1)
        grid1.addWidget(self.brand_input, 3, 1)
        grid1.addWidget(self._field("Description"), 4, 0, 1, 2)
        grid1.addWidget(self.description_input, 5, 0, 1, 2)

        section1.layout().addLayout(grid1)
        form.addWidget(section1)

        # === Section: Prix et taxes ===
        section2 = self._create_section("Prix et taxes")
        grid2 = QGridLayout()
        grid2.setSpacing(16)
        grid2.setColumnStretch(0, 1)
        grid2.setColumnStretch(1, 1)
        grid2.setColumnStretch(2, 1)

        self.purchase_price_input = QLineEdit("0")
        self.sale_price_input = QLineEdit()
        self.sale_price_input.setPlaceholderText("Prix de vente")
        self.tax_rate_input = QLineEdit("0")

        grid2.addWidget(self._field("Prix d'achat (FCFA)"), 0, 0)
        grid2.addWidget(self.purchase_price_input, 1, 0)
        grid2.addWidget(self._field("Prix de vente (FCFA) *"), 0, 1)
        grid2.addWidget(self.sale_price_input, 1, 1)
        grid2.addWidget(self._field("TVA (%)"), 0, 2)
        grid2.addWidget(self.tax_rate_input, 1, 2)

        section2.layout().addLayout(grid2)
        form.addWidget(section2)

        # === Section: Stock ===
        section3 = self._create_section("Gestion du stock")
        grid3 = QGridLayout()
        grid3.setSpacing(16)

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 1_000_000)
        self.stock_min_input = QSpinBox()
        self.stock_min_input.setRange(0, 1_000_000)
        self.stock_max_input = QSpinBox()
        self.stock_max_input.setRange(0, 1_000_000)
        self.unit_input = QComboBox()
        self.unit_input.addItems(["piece", "kg", "litre", "paquet"])

        grid3.addWidget(self._field("Stock actuel"), 0, 0)
        grid3.addWidget(self.stock_input, 1, 0)
        grid3.addWidget(self._field("Stock minimum"), 0, 1)
        grid3.addWidget(self.stock_min_input, 1, 1)
        grid3.addWidget(self._field("Stock maximum"), 0, 2)
        grid3.addWidget(self.stock_max_input, 1, 2)
        grid3.addWidget(self._field("Unite"), 0, 3)
        grid3.addWidget(self.unit_input, 1, 3)

        section3.layout().addLayout(grid3)
        form.addWidget(section3)

        # === Section: Autres informations ===
        section4 = self._create_section("Autres informations")
        grid4 = QGridLayout()
        grid4.setSpacing(16)

        self.expiration_input = QDateEdit()
        self.expiration_input.setCalendarPopup(True)
        self.expiration_input.setDate(QDate.currentDate())
        self.category_id_input = QSpinBox()
        self.category_id_input.setRange(0, 999999)
        self.supplier_id_input = QSpinBox()
        self.supplier_id_input.setRange(0, 999999)
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Chemin vers l'image...")
        self.promotion_eligible_check = QCheckBox("Eligible aux promotions")
        self.promotion_eligible_check.setChecked(True)

        grid4.addWidget(self._field("Date d'expiration"), 0, 0)
        grid4.addWidget(self.expiration_input, 1, 0)
        grid4.addWidget(self._field("Categorie (ID)"), 0, 1)
        grid4.addWidget(self.category_id_input, 1, 1)
        grid4.addWidget(self._field("Fournisseur (ID)"), 0, 2)
        grid4.addWidget(self.supplier_id_input, 1, 2)
        grid4.addWidget(self._field("Chemin image"), 2, 0, 1, 3)
        grid4.addWidget(self.image_path_input, 3, 0, 1, 3)
        grid4.addWidget(self.promotion_eligible_check, 4, 0, 1, 3)

        section4.layout().addLayout(grid4)
        form.addWidget(section4)
        form.addStretch()

        scroll.setWidget(form_container)
        main_layout.addWidget(scroll, 1)

        # Footer avec boutons
        footer = QWidget()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 16, 28, 16)
        footer_layout.setSpacing(12)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E2E8F0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Enregistrer le produit")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1D4ED8;
            }
        """)
        save_btn.clicked.connect(self.accept)

        footer_layout.addStretch()
        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(save_btn)
        main_layout.addWidget(footer)

    def _field(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; letter-spacing: 0.3px;")
        return lbl

    def _create_section(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                color: #0F172A;
                padding-top: 24px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
                background: #FFFFFF;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        return group


class PromotionCreateDialog(QDialog):
    def __init__(self, products: list[Product], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Creer une promotion")
        self.setModal(True)
        self.setMinimumSize(480, 400)
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #374151; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563EB; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(28, 24, 28, 20)
        title = QLabel("Nouvelle promotion")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        h_layout.addWidget(title)
        main_layout.addWidget(header)

        # Form
        form_widget = QWidget()
        form = QVBoxLayout(form_widget)
        form.setContentsMargins(28, 24, 28, 24)
        form.setSpacing(16)

        self.product_box = QComboBox()
        for p in products:
            self.product_box.addItem(f"{p.name} ({p.barcode})", p.id)

        self.type_box = QComboBox()
        self.type_box.addItem("Pourcentage (%)", PromotionType.PERCENTAGE)
        self.type_box.addItem("Montant fixe (FCFA)", PromotionType.FIXED)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Promo weekend")
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Ex: 10")

        form.addWidget(QLabel("Nom de la promotion"))
        form.addWidget(self.name_input)
        form.addWidget(QLabel("Produit concerne"))
        form.addWidget(self.product_box)
        form.addWidget(QLabel("Type de remise"))
        form.addWidget(self.type_box)
        form.addWidget(QLabel("Valeur"))
        form.addWidget(self.value_input)
        form.addStretch()

        main_layout.addWidget(form_widget, 1)

        # Footer
        footer = QWidget()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(28, 16, 28, 16)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("background: #F1F5F9; color: #475569; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Creer la promotion")
        save_btn.setStyleSheet("background: #2563EB; color: #FFFFFF; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;")
        save_btn.clicked.connect(self.accept)
        f_layout.addStretch()
        f_layout.addWidget(cancel_btn)
        f_layout.addWidget(save_btn)
        main_layout.addWidget(footer)


class UserCreateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Creer un utilisateur")
        self.setModal(True)
        self.setMinimumSize(500, 520)
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #374151; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563EB; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(28, 24, 28, 20)
        title = QLabel("Nouvel utilisateur")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        h_layout.addWidget(title)
        main_layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F8FAFC; border: none; }")

        form_widget = QWidget()
        form = QVBoxLayout(form_widget)
        form.setContentsMargins(28, 24, 28, 24)
        form.setSpacing(16)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ex: jdupont")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe securise")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex: Dupont")
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Ex: Jean")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Ex: EMP001")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Ex: +221 77 123 45 67")

        self.role_box = QComboBox()
        self.role_box.addItem("Administrateur", UserRole.ADMIN)
        self.role_box.addItem("Superviseur", UserRole.SUPERVISOR)
        self.role_box.addItem("Caissier", UserRole.CASHIER)

        for lbl, widget in [
            ("Nom d'utilisateur", self.username_input),
            ("Mot de passe", self.password_input),
            ("Nom de famille", self.nom_input),
            ("Prenom", self.prenom_input),
            ("Code employe", self.code_input),
            ("Telephone", self.phone_input),
            ("Role", self.role_box),
        ]:
            form.addWidget(QLabel(lbl))
            form.addWidget(widget)
        form.addStretch()

        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll, 1)

        # Footer
        footer = QWidget()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(28, 16, 28, 16)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("background: #F1F5F9; color: #475569; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Creer l'utilisateur")
        save_btn.setStyleSheet("background: #2563EB; color: #FFFFFF; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600;")
        save_btn.clicked.connect(self.accept)
        f_layout.addStretch()
        f_layout.addWidget(cancel_btn)
        f_layout.addWidget(save_btn)
        main_layout.addWidget(footer)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD - Interface principale
# ══════════════════════════════════════════════════════════════════════════════

class AdminDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self._pos_windows: list[POSScreen] = []
        self.setWindowTitle("MOKAT MARKET — Administration")
        self.resize(1400, 900)
        self.setStyleSheet("background: #F1F5F9;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════════════════════
        # SIDEBAR - Navigation gauche
        # ══════════════════════════════════════════════════════════════════════
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0F172A, stop:1 #1E293B);
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo / Brand
        brand = QWidget()
        brand.setStyleSheet("background: transparent;")
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(24, 28, 24, 28)
        brand_layout.setSpacing(12)

        logo_circle = QLabel("M")
        logo_circle.setFixedSize(42, 42)
        logo_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_circle.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #3B82F6, stop:1 #1D4ED8);
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 800;
            border-radius: 10px;
        """)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        brand_name = QLabel("MOKAT")
        brand_name.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1px; background: transparent;")
        brand_tagline = QLabel("MARKET")
        brand_tagline.setStyleSheet("color: #3B82F6; font-size: 11px; font-weight: 600; letter-spacing: 2px; background: transparent;")
        brand_text.addWidget(brand_name)
        brand_text.addWidget(brand_tagline)
        brand_layout.addWidget(logo_circle)
        brand_layout.addLayout(brand_text)
        brand_layout.addStretch()
        sidebar_layout.addWidget(brand)

        # Navigation header
        nav_header = QLabel("MENU PRINCIPAL")
        nav_header.setStyleSheet("""
            color: #64748B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 20px 24px 12px 24px;
            background: transparent;
        """)
        sidebar_layout.addWidget(nav_header)

        # Menu items
        self.menu = QListWidget()
        self.menu.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 0 12px;
            }
            QListWidget::item {
                color: #94A3B8;
                background: transparent;
                border-radius: 10px;
                padding: 14px 16px;
                margin: 2px 0;
                font-size: 13px;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background: rgba(59, 130, 246, 0.1);
                color: #E2E8F0;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #2563EB);
                color: #FFFFFF;
                font-weight: 600;
            }
        """)
        self._populate_sidebar()
        sidebar_layout.addWidget(self.menu, 1)

        # User footer
        user_footer = QWidget()
        user_footer.setStyleSheet("background: rgba(15, 23, 42, 0.5); border-top: 1px solid #1E293B;")
        uf_layout = QHBoxLayout(user_footer)
        uf_layout.setContentsMargins(20, 16, 20, 20)
        uf_layout.setSpacing(12)

        avatar = QLabel(user.prenom[0].upper() if user.prenom else "A")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #10B981, stop:1 #059669);
            color: #FFFFFF;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
        """)

        user_info = QVBoxLayout()
        user_info.setSpacing(2)
        user_name = QLabel(f"{user.prenom} {user.nom}")
        user_name.setStyleSheet("color: #F1F5F9; font-size: 13px; font-weight: 600; background: transparent;")
        user_role = QLabel("Administrateur")
        user_role.setStyleSheet("color: #64748B; font-size: 11px; background: transparent;")
        user_info.addWidget(user_name)
        user_info.addWidget(user_role)

        logout_btn = QPushButton("Deconnexion")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #EF4444;
                color: #FFFFFF;
            }
        """)
        logout_btn.clicked.connect(self.close)

        uf_layout.addWidget(avatar)
        uf_layout.addLayout(user_info, 1)
        uf_layout.addWidget(logout_btn)
        sidebar_layout.addWidget(user_footer)

        root.addWidget(sidebar)

        # ══════════════════════════════════════════════════════════════════════
        # MAIN CONTENT
        # ══════════════════════════════════════════════════════════════════════
        content = QWidget()
        content.setStyleSheet("background: #F1F5F9;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Topbar
        topbar = self._build_topbar()
        content_layout.addWidget(topbar)

        # Pages stack
        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.products_page = self._build_products_page()
        self.promotions_page = self._build_placeholder_page("Promotions", "Gestion des promotions et remises")
        self.users_page = self._build_placeholder_page("Utilisateurs", "Gestion des comptes utilisateurs")
        self.stock_page = self._build_stock_page()
        self.pos_page = self._build_pos_page()
        self.reports_page = self._build_placeholder_page("Rapports", "Analyses et statistiques")
        self.settings_page = self._build_placeholder_page("Parametres", "Configuration du systeme")

        for page in [
            self.dashboard_page, self.products_page, self.promotions_page,
            self.users_page, self.stock_page, self.pos_page,
            self.reports_page, self.settings_page,
        ]:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack, 1)
        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)

        root.addWidget(content, 1)
        self.refresh_dashboard()

    def _populate_sidebar(self) -> None:
        items = [
            ("Dashboard", "Vue d'ensemble"),
            ("Produits", "Catalogue"),
            ("Promotions", "Remises"),
            ("Utilisateurs", "Equipe"),
            ("Stock", "Inventaire"),
            ("Caisse", "Point de vente"),
            ("Rapports", "Analyses"),
            ("Parametres", "Config"),
        ]
        for name, _ in items:
            item = QListWidgetItem(name)
            self.menu.addItem(item)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(72)
        bar.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(16)

        # Search
        search_container = QWidget()
        search_container.setStyleSheet("background: #F8FAFC; border-radius: 12px;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 0, 16, 0)
        search_layout.setSpacing(10)

        search_icon = QLabel("Q")
        search_icon.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #94A3B8; background: transparent;"
        )
        self.topbar_search = QLineEdit()
        self.topbar_search.setPlaceholderText("Rechercher un produit, code-barres...")
        self.topbar_search.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                font-size: 13px;
                color: #374151;
                padding: 12px 0;
            }
        """)
        self.topbar_search.setFixedWidth(280)
        self.topbar_search.returnPressed.connect(self._search_products)
        self.topbar_search.textChanged.connect(self._search_products)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.topbar_search)
        layout.addWidget(search_container)
        layout.addStretch()

        # Quick actions
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        refresh_btn.clicked.connect(self.refresh_dashboard)
        layout.addWidget(refresh_btn)

        # Notifications bell
        notif_btn = QPushButton("--")
        notif_btn.setFixedSize(40, 40)
        notif_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                border: none;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                color: #64748B;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        layout.addWidget(notif_btn)

        # User avatar in topbar
        user_btn = QLabel(f"{self.user.prenom[0]}{self.user.nom[0]}")
        user_btn.setFixedSize(40, 40)
        user_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_btn.setStyleSheet("""
            background: #3B82F6;
            color: #FFFFFF;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
        """)
        layout.addWidget(user_btn)

        return bar

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        # Page header
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("Tableau de bord")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        subtitle = QLabel(f"Bienvenue, {self.user.prenom}. Voici un apercu de votre activite.")
        subtitle.setStyleSheet("font-size: 14px; color: #64748B;")
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        # Quick action buttons
        quick_add = QPushButton("+ Nouveau produit")
        quick_add.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        quick_add.clicked.connect(self._create_product)
        header.addWidget(quick_add)
        layout.addLayout(header)

        # Stat cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.total_products_label = self._create_stat_card(
            cards_layout, "Total produits", "0", "#3B82F6", "Produits"
        )
        self.low_stock_label = self._create_stat_card(
            cards_layout, "Stock faible", "0", "#F59E0B", "Alerte"
        )
        self.active_promotions_label = self._create_stat_card(
            cards_layout, "Promotions actives", "0", "#10B981", "Promo"
        )
        self.sales_today_label = self._create_stat_card(
            cards_layout, "Ventes du jour", "0 FCFA", "#8B5CF6", "Ventes"
        )
        layout.addLayout(cards_layout)

        # Actions row
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(24, 20, 24, 20)
        actions_layout.setSpacing(16)

        actions_title = QLabel("Actions rapides")
        actions_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        actions_layout.addWidget(actions_title)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un produit...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #3B82F6; }
        """)
        self.search_input.returnPressed.connect(self._search_products)
        self.search_input.textChanged.connect(self._search_products)

        for text, handler, style in [
            ("+ Produit", self._create_product, "primary"),
            ("+ Promotion", self._create_promotion, "secondary"),
            ("+ Utilisateur", self._create_user, "secondary"),
            ("Ouvrir Caisse", self._open_pos_screen, "success"),
        ]:
            btn = QPushButton(text)
            if style == "primary":
                btn.setStyleSheet("""
                    QPushButton {
                        background: #2563EB; color: #FFFFFF; border: none;
                        border-radius: 10px; padding: 12px 20px; font-weight: 600;
                    }
                    QPushButton:hover { background: #1D4ED8; }
                """)
            elif style == "success":
                btn.setStyleSheet("""
                    QPushButton {
                        background: #10B981; color: #FFFFFF; border: none;
                        border-radius: 10px; padding: 12px 20px; font-weight: 600;
                    }
                    QPushButton:hover { background: #059669; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #F1F5F9; color: #475569; border: none;
                        border-radius: 10px; padding: 12px 20px; font-weight: 600;
                    }
                    QPushButton:hover { background: #E2E8F0; }
                """)
            btn.clicked.connect(handler)
            buttons_row.addWidget(btn)

        buttons_row.insertWidget(0, self.search_input, 1)
        actions_layout.addLayout(buttons_row)
        layout.addWidget(actions_card)

        # Search results table
        table_card = QFrame()
        table_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(24, 20, 24, 20)

        table_header = QLabel("Resultats de recherche")
        table_header.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        table_layout.addWidget(table_header)

        self.search_table = QTableWidget(0, 7)
        self.search_table.setHorizontalHeaderLabels(["ID", "Code-barres", "Ref", "Nom", "Marque", "Prix", "Stock"])
        self._style_table(self.search_table)
        table_layout.addWidget(self.search_table)
        layout.addWidget(table_card, 1)

        # Bottom row: notifications + activity
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        for title_text, widget_name in [("Alertes systeme", "notifications"), ("Activite recente", "activity")]:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 20, 24, 20)
            card_title = QLabel(title_text)
            card_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
            card_layout.addWidget(card_title)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(140)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    padding: 12px;
                    font-size: 12px;
                    color: #475569;
                }
            """)
            card_layout.addWidget(text_edit)
            if widget_name == "notifications":
                self.notifications_box = text_edit
            else:
                self.activity_box = text_edit
            bottom_row.addWidget(card)

        layout.addLayout(bottom_row)

        scroll.setWidget(content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _create_stat_card(self, parent_layout: QHBoxLayout, title: str, value: str, color: str, icon: str) -> QLabel:
        card = QFrame()
        card.setMinimumWidth(200)
        card.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                border-left: 4px solid {color};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(8)

        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        top_row.addWidget(icon_lbl)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;")
        card_layout.addWidget(title_lbl)

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"font-size: 32px; font-weight: 800; color: {color};")
        card_layout.addWidget(value_lbl)

        parent_layout.addWidget(card)
        return value_lbl

    def _style_table(self, table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #F1F5F9;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:selected {
                background: #EFF6FF;
                color: #1E40AF;
            }
            QTableWidget::item:alternate {
                background: #F8FAFC;
            }
            QHeaderView::section {
                background: #F8FAFC;
                color: #64748B;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 14px 12px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
            }
        """)

    def _build_products_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Gestion des produits")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Actions card
        actions_card = QFrame()
        actions_card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 16, 20, 16)
        actions_layout.setSpacing(12)

        self.products_search_input = QLineEdit()
        self.products_search_input.setPlaceholderText("Rechercher un produit...")
        self.products_search_input.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px;
                padding: 12px 16px; font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #3B82F6; }
        """)
        self.products_search_input.textChanged.connect(self._refresh_products_table)

        btn_add = QPushButton("+ Ajouter")
        btn_add.setStyleSheet("QPushButton { background: #2563EB; color: #FFFFFF; border: none; border-radius: 10px; padding: 12px 20px; font-weight: 600; } QPushButton:hover { background: #1D4ED8; }")
        btn_add.clicked.connect(self._create_product)

        btn_toggle = QPushButton("Activer / Desactiver")
        btn_toggle.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: none; border-radius: 10px; padding: 12px 20px; font-weight: 600; } QPushButton:hover { background: #E2E8F0; }")
        btn_toggle.clicked.connect(self._toggle_selected_product_status)

        btn_delete = QPushButton("Supprimer")
        btn_delete.setStyleSheet("QPushButton { background: #FEE2E2; color: #DC2626; border: none; border-radius: 10px; padding: 12px 20px; font-weight: 600; } QPushButton:hover { background: #FECACA; }")
        btn_delete.clicked.connect(self._delete_selected_product)

        actions_layout.addWidget(self.products_search_input, 1)
        actions_layout.addWidget(btn_add)
        actions_layout.addWidget(btn_toggle)
        actions_layout.addWidget(btn_delete)
        layout.addWidget(actions_card)

        # Table card
        table_card = QFrame()
        table_card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)

        self.products_table = QTableWidget(0, 9)
        self.products_table.setHorizontalHeaderLabels(["ID", "Code-barres", "Ref", "Nom", "Marque", "Prix vente", "Stock", "Stock min", "Statut"])
        self._style_table(self.products_table)
        table_layout.addWidget(self.products_table)
        layout.addWidget(table_card, 1)

        scroll.setWidget(content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_stock_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        title = QLabel("Gestion du stock")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        layout.addWidget(title)

        # Actions
        actions_card = QFrame()
        actions_card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 16, 20, 16)
        actions_layout.setSpacing(12)

        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Rechercher...")
        self.stock_search_input.setStyleSheet("QLineEdit { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; } QLineEdit:focus { border: 2px solid #3B82F6; }")
        self.stock_search_input.textChanged.connect(self._refresh_stock_table)

        btn_entry = QPushButton("+ Entree")
        btn_entry.setStyleSheet("QPushButton { background: #10B981; color: #FFFFFF; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; } QPushButton:hover { background: #059669; }")
        btn_entry.clicked.connect(lambda: self._record_stock_movement(StockMovementType.ENTRY))

        btn_loss = QPushButton("Sortie / Perte")
        btn_loss.setStyleSheet("QPushButton { background: #FEE2E2; color: #DC2626; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; } QPushButton:hover { background: #FECACA; }")
        btn_loss.clicked.connect(lambda: self._record_stock_movement(StockMovementType.LOSS))

        btn_adjust = QPushButton("Ajustement")
        btn_adjust.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; } QPushButton:hover { background: #E2E8F0; }")
        btn_adjust.clicked.connect(lambda: self._record_stock_movement(StockMovementType.ADJUSTMENT))

        btn_restock = QPushButton("Renouveler")
        btn_restock.setStyleSheet("QPushButton { background: #2563EB; color: #FFFFFF; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; } QPushButton:hover { background: #1D4ED8; }")
        btn_restock.clicked.connect(self._restock_selected_product)

        btn_exact = QPushButton("Inventaire")
        btn_exact.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; } QPushButton:hover { background: #E2E8F0; }")
        btn_exact.clicked.connect(self._set_selected_stock)

        actions_layout.addWidget(self.stock_search_input, 1)
        for btn in [btn_entry, btn_loss, btn_adjust, btn_restock, btn_exact]:
            actions_layout.addWidget(btn)
        layout.addWidget(actions_card)

        # Stock table
        table_card = QFrame()
        table_card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)

        self.stock_table = QTableWidget(0, 9)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Code-barres", "Nom", "Stock", "Min", "Max", "Unite", "Expiration", "Statut"])
        self._style_table(self.stock_table)
        table_layout.addWidget(self.stock_table)
        layout.addWidget(table_card, 1)

        # History
        history_card = QFrame()
        history_card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(20, 20, 20, 20)

        history_title = QLabel("Historique des mouvements")
        history_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        history_layout.addWidget(history_title)

        self.stock_history_table = QTableWidget(0, 6)
        self.stock_history_table.setHorizontalHeaderLabels(["Date", "Produit", "Type", "Quantite", "Raison", "Utilisateur"])
        self._style_table(self.stock_history_table)
        self.stock_history_table.setMaximumHeight(200)
        history_layout.addWidget(self.stock_history_table)
        layout.addWidget(history_card)

        scroll.setWidget(content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_pos_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        title = QLabel("Interface Caisse")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(20)

        icon_lbl = QLabel("🛒")
        icon_lbl.setStyleSheet("font-size: 48px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_lbl)

        info = QLabel("Ouvrez l'interface de caisse tactile pour scanner les produits,\nencaisser les clients et imprimer les tickets.")
        info.setStyleSheet("color: #64748B; font-size: 15px; text-align: center;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setWordWrap(True)
        card_layout.addWidget(info)

        open_btn = QPushButton("Ouvrir l'interface de caisse")
        open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        open_btn.clicked.connect(self._open_pos_screen)
        card_layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_placeholder_page(self, module_name: str, description: str) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: #F1F5F9;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel(module_name)
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("🚧")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon)

        text = QLabel(f"{description}\n\nCe module est en cours de developpement.")
        text.setStyleSheet("color: #64748B; font-size: 14px; text-align: center;")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(text)

        layout.addWidget(card)
        layout.addStretch()
        return page

    # ══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

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
            notifications.append(f"⚠️ {low_stock} produit(s) sous le stock minimum.")
        expired = [p for p in products if p.expiration_date and p.expiration_date <= date.today()]
        near_exp = [p for p in products if p.expiration_date and 0 <= (p.expiration_date - date.today()).days <= 7]
        if expired:
            notifications.append(f"❌ {len(expired)} produit(s) expire(s).")
        if near_exp:
            notifications.append(f"ℹ️ {len(near_exp)} produit(s) expirent sous 7 jours.")
        if not notifications:
            notifications.append("✅ Aucun incident critique detecte.")
        self.notifications_box.setPlainText("\n".join(notifications))

    def _load_recent_activity(self) -> None:
        entries: list[tuple[str, object]] = []
        with SessionLocal() as session:
            products = ProductRepository(session).latest_created(5)
            promotions = PromotionRepository(session).latest_created(5)
            users = UserRepository(session).latest_created(5)
            for p in products:
                entries.append((f"📦 Produit ajoute: {p.name}", p.created_at))
            for promo in promotions:
                entries.append((f"🏷️ Promotion creee: {promo.name}", promo.created_at))
            for u in users:
                entries.append((f"👤 Utilisateur cree: {u.username}", u.created_at))

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
            status = "🔴 RUPTURE" if p.stock_quantity <= 0 else ("🟡 FAIBLE" if p.stock_quantity <= p.stock_min else "🟢 OK")
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
                QMessageBox.warning(self, "Erreur", "Impossible de mettre a jour le stock")
                return
            session.add(
                StockMovement(
                    product_id=product_id,
                    type=StockMovementType.ADJUSTMENT,
                    quantity=qty - old_qty,
                    reason=f"inventaire: {old_qty} -> {qty}",
                    user_id=self.user.id,
                )
            )
            session.commit()
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        stats = self._load_stats()
        self.total_products_label.setText(str(stats.total_products))
        self.low_stock_label.setText(str(stats.low_stock_products))
        self.active_promotions_label.setText(str(stats.active_promotions))
        self.sales_today_label.setText(f"{stats.sales_today:,.0f}")
        self._load_notifications()
        self._load_recent_activity()
        self._search_products()
        if self.stack.currentIndex() == 1:
            self._refresh_products_table()
        if self.stack.currentIndex() == 4:
            self._refresh_stock_table()
            self._refresh_stock_history()
