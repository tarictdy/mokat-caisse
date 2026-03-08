from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from models.product import Product
from models.promotion import Promotion, PromotionType
from models.user import User, UserRole
from repositories.product_repo import ProductRepository
from repositories.promotion_repo import PromotionRepository
from repositories.sale_repo import SaleRepository
from repositories.user_repo import UserRepository
from services.product_service import ProductService
from services.user_service import UserService


@dataclass
class DashboardStats:
    total_products: int
    low_stock_products: int
    active_promotions: int
    sales_today: Decimal


class ProductCreateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter produit")
        self.setModal(True)

        self.barcode_input = QLineEdit()
        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.stock_input = QSpinBox()
        self.stock_input.setMinimum(0)
        self.stock_input.setMaximum(1_000_000)

        form = QFormLayout(self)
        form.addRow("Code-barres", self.barcode_input)
        form.addRow("Nom", self.name_input)
        form.addRow("Prix de vente", self.price_input)
        form.addRow("Stock initial", self.stock_input)

        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


class PromotionCreateDialog(QDialog):
    def __init__(self, products: list[Product], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Créer promotion")
        self.setModal(True)

        self.product_box = QComboBox()
        for p in products:
            self.product_box.addItem(f"{p.name} ({p.barcode})", p.id)

        self.type_box = QComboBox()
        self.type_box.addItem("Pourcentage", PromotionType.PERCENTAGE)
        self.type_box.addItem("Montant fixe", PromotionType.FIXED)

        self.name_input = QLineEdit()
        self.value_input = QLineEdit()

        form = QFormLayout(self)
        form.addRow("Nom promotion", self.name_input)
        form.addRow("Produit", self.product_box)
        form.addRow("Type", self.type_box)
        form.addRow("Valeur", self.value_input)

        save_btn = QPushButton("Créer")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


class UserCreateDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Créer utilisateur")
        self.setModal(True)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.code_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.role_box = QComboBox()
        self.role_box.addItem("Admin", UserRole.ADMIN)
        self.role_box.addItem("Superviseur", UserRole.SUPERVISOR)
        self.role_box.addItem("Caissier", UserRole.CASHIER)

        form = QFormLayout(self)
        form.addRow("Username", self.username_input)
        form.addRow("Mot de passe", self.password_input)
        form.addRow("Nom", self.nom_input)
        form.addRow("Prénom", self.prenom_input)
        form.addRow("Code employé", self.code_input)
        form.addRow("Téléphone", self.phone_input)
        form.addRow("Rôle", self.role_box)

        save_btn = QPushButton("Créer")
        save_btn.clicked.connect(self.accept)
        form.addWidget(save_btn)


class AdminDashboard(QWidget):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle("Dashboard Admin")
        self.resize(1200, 760)

        root = QHBoxLayout(self)

        self.menu = QListWidget()
        self.menu.setFixedWidth(230)
        for label in ["Dashboard", "Produits", "Promotions", "Utilisateurs", "Stock", "Rapports", "Paramètres"]:
            QListWidgetItem(label, self.menu)

        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.stack.addWidget(self.dashboard_page)

        for label in ["Produits", "Promotions", "Utilisateurs", "Stock", "Rapports", "Paramètres"]:
            self.stack.addWidget(self._build_placeholder_page(label))

        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)

        root.addWidget(self.menu)
        root.addWidget(self.stack, 1)

        self.refresh_dashboard()

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(f"Bienvenue {self.user.prenom} {self.user.nom} — Centre de contrôle")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Cartes statistiques
        cards = QGridLayout()
        self.total_products_label = self._create_stat_card(cards, 0, 0, "Produits total")
        self.low_stock_label = self._create_stat_card(cards, 0, 1, "Produits en rupture / min")
        self.active_promotions_label = self._create_stat_card(cards, 0, 2, "Promotions actives")
        self.sales_today_label = self._create_stat_card(cards, 0, 3, "Ventes du jour")
        layout.addLayout(cards)

        # Recherche rapide + actions
        control_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Recherche rapide produit (nom ou code-barres)")
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self._search_products)

        add_product_btn = QPushButton("+ Ajouter produit")
        add_product_btn.clicked.connect(self._create_product)
        add_promo_btn = QPushButton("+ Créer promotion")
        add_promo_btn.clicked.connect(self._create_promotion)
        add_user_btn = QPushButton("+ Nouvel utilisateur")
        add_user_btn.clicked.connect(self._create_user)

        control_row.addWidget(self.search_input, 1)
        control_row.addWidget(search_button)
        control_row.addWidget(add_product_btn)
        control_row.addWidget(add_promo_btn)
        control_row.addWidget(add_user_btn)
        layout.addLayout(control_row)

        # Tableau de recherche
        self.search_table = QTableWidget(0, 5)
        self.search_table.setHorizontalHeaderLabels(["Barcode", "Nom", "Prix", "Stock", "Statut"])
        layout.addWidget(self.search_table)

        # Notifications + activité récente
        bottom = QHBoxLayout()
        self.notifications_box = QTextEdit()
        self.notifications_box.setReadOnly(True)
        self.activity_box = QTextEdit()
        self.activity_box.setReadOnly(True)

        notif_group = QGroupBox("Notifications système")
        notif_layout = QVBoxLayout(notif_group)
        notif_layout.addWidget(self.notifications_box)

        activity_group = QGroupBox("Activité récente")
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.addWidget(self.activity_box)

        bottom.addWidget(notif_group)
        bottom.addWidget(activity_group)
        layout.addLayout(bottom)

        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return page

    def _build_placeholder_page(self, module_name: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(f"Module {module_name} — en cours d'implémentation"))
        return page

    def _create_stat_card(self, grid: QGridLayout, row: int, col: int, title: str) -> QLabel:
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        label = QLabel("0")
        label.setStyleSheet("font-size: 28px; font-weight: bold;")
        box_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(box, row, col)
        return label

    def _on_menu_changed(self, row: int) -> None:
        if row < 0:
            return
        self.stack.setCurrentIndex(row)

    def _load_stats(self) -> DashboardStats:
        with SessionLocal() as session:
            product_repo = ProductRepository(session)
            promotion_repo = PromotionRepository(session)
            sale_repo = SaleRepository(session)

            return DashboardStats(
                total_products=product_repo.count_all(),
                low_stock_products=product_repo.count_low_stock(),
                active_promotions=promotion_repo.count_active(date.today()),
                sales_today=sale_repo.total_sales_for_day(date.today()),
            )

    def _fill_search_results(self, products: list[Product]) -> None:
        self.search_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.search_table.setItem(row, 0, QTableWidgetItem(p.barcode))
            self.search_table.setItem(row, 1, QTableWidgetItem(p.name))
            self.search_table.setItem(row, 2, QTableWidgetItem(str(p.sale_price)))
            self.search_table.setItem(row, 3, QTableWidgetItem(str(p.stock_quantity)))
            self.search_table.setItem(row, 4, QTableWidgetItem(p.status.value))

    def _load_notifications(self) -> None:
        with SessionLocal() as session:
            product_repo = ProductRepository(session)
            low_stock = product_repo.count_low_stock()
            near_expiry_promotions = 0

            notifications: list[str] = []
            if low_stock > 0:
                notifications.append(f"⚠ {low_stock} produit(s) en rupture ou sous stock minimum.")
            if near_expiry_promotions > 0:
                notifications.append(f"ℹ {near_expiry_promotions} promotion(s) arrivent à expiration.")
            if not notifications:
                notifications.append("✅ Aucun incident critique détecté.")

            self.notifications_box.setPlainText("\n".join(notifications))

    def _load_recent_activity(self) -> None:
        entries: list[tuple[str, object]] = []
        with SessionLocal() as session:
            products = ProductRepository(session).latest_created(limit=5)
            promotions = PromotionRepository(session).latest_created(limit=5)
            users = UserRepository(session).latest_created(limit=5)

            for p in products:
                entries.append((f"Produit ajouté: {p.name}", p.created_at))
            for promo in promotions:
                entries.append((f"Promotion créée: {promo.name}", promo.created_at))
            for u in users:
                entries.append((f"Utilisateur créé: {u.username}", u.created_at))

        entries.sort(key=lambda item: item[1], reverse=True)
        self.activity_box.setPlainText("\n".join(msg for msg, _ in entries[:10]) or "Aucune activité récente.")

    def _search_products(self) -> None:
        query = self.search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            if query:
                products = repo.search_by_name_or_barcode(query)
            else:
                products = repo.list_all()[:20]
        self._fill_search_results(products)

    def _create_product(self) -> None:
        dialog = ProductCreateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            sale_price = Decimal(dialog.price_input.text().strip())
        except Exception:
            QMessageBox.warning(self, "Erreur", "Prix invalide")
            return

        with SessionLocal() as session:
            service = ProductService(ProductRepository(session))
            try:
                service.create_product(
                    barcode=dialog.barcode_input.text().strip(),
                    name=dialog.name_input.text().strip(),
                    sale_price=sale_price,
                    stock_quantity=dialog.stock_input.value(),
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

        promo_type: PromotionType = dialog.type_box.currentData()
        value_text = dialog.value_input.text().strip()
        if not value_text:
            QMessageBox.warning(self, "Erreur", "Valeur de promotion requise")
            return

        with SessionLocal() as session:
            repo = PromotionRepository(session)
            promo = Promotion(
                name=dialog.name_input.text().strip() or "Promo",
                product_id=int(dialog.product_box.currentData()),
                type=promo_type,
                percentage_discount=Decimal(value_text) if promo_type == PromotionType.PERCENTAGE else None,
                fixed_discount=Decimal(value_text) if promo_type == PromotionType.FIXED else None,
                start_date=date.today(),
                end_date=date.today(),
                active=True,
            )
            repo.add(promo)
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

    def refresh_dashboard(self) -> None:
        stats = self._load_stats()
        self.total_products_label.setText(str(stats.total_products))
        self.low_stock_label.setText(str(stats.low_stock_products))
        self.active_promotions_label.setText(str(stats.active_promotions))
        self.sales_today_label.setText(f"{stats.sales_today:.2f}")
        self._search_products()
        self._load_notifications()
        self._load_recent_activity()
