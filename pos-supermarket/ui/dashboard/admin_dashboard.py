from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from models.product import Product, ProductStatus
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
        self.resize(500, 560)

        self.barcode_input = QLineEdit()
        self.reference_input = QLineEdit()
        self.name_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.description_input = QLineEdit()

        self.purchase_price_input = QLineEdit("0")
        self.sale_price_input = QLineEdit()
        self.tax_rate_input = QLineEdit("0")

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 1_000_000)
        self.stock_min_input = QSpinBox()
        self.stock_min_input.setRange(0, 1_000_000)
        self.stock_max_input = QSpinBox()
        self.stock_max_input.setRange(0, 1_000_000)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["piece", "kg", "litre", "paquet"])

        self.expiration_input = QDateEdit()
        self.expiration_input.setCalendarPopup(True)
        self.expiration_input.setDate(QDate.currentDate())

        self.category_id_input = QSpinBox()
        self.category_id_input.setRange(0, 999999)
        self.supplier_id_input = QSpinBox()
        self.supplier_id_input.setRange(0, 999999)

        self.image_path_input = QLineEdit()
        self.promotion_eligible_check = QCheckBox("Éligible aux promotions")
        self.promotion_eligible_check.setChecked(True)

        form = QFormLayout(self)
        form.addRow("Nom du produit *", self.name_input)
        form.addRow("Code-barres *", self.barcode_input)
        form.addRow("Référence interne", self.reference_input)
        form.addRow("Catégorie (ID)", self.category_id_input)
        form.addRow("Marque", self.brand_input)
        form.addRow("Description", self.description_input)
        form.addRow("Prix d'achat", self.purchase_price_input)
        form.addRow("Prix de vente *", self.sale_price_input)
        form.addRow("TVA (%)", self.tax_rate_input)
        form.addRow("Stock actuel", self.stock_input)
        form.addRow("Stock minimum", self.stock_min_input)
        form.addRow("Stock maximum", self.stock_max_input)
        form.addRow("Unité", self.unit_input)
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
        self.resize(1300, 800)

        root = QHBoxLayout(self)

        self.menu = QListWidget()
        self.menu.setFixedWidth(230)
        for label in ["Dashboard", "Produits", "Promotions", "Utilisateurs", "Stock", "Rapports", "Paramètres"]:
            QListWidgetItem(label, self.menu)

        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.products_page = self._build_products_page()
        self.promotions_page = self._build_placeholder_page("Promotions")
        self.users_page = self._build_placeholder_page("Utilisateurs")
        self.stock_page = self._build_stock_page()
        self.reports_page = self._build_placeholder_page("Rapports")
        self.settings_page = self._build_placeholder_page("Paramètres")

        for page in [
            self.dashboard_page,
            self.products_page,
            self.promotions_page,
            self.users_page,
            self.stock_page,
            self.reports_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

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

        cards = QGridLayout()
        self.total_products_label = self._create_stat_card(cards, 0, 0, "Produits total")
        self.low_stock_label = self._create_stat_card(cards, 0, 1, "Produits en rupture / min")
        self.active_promotions_label = self._create_stat_card(cards, 0, 2, "Promotions actives")
        self.sales_today_label = self._create_stat_card(cards, 0, 3, "Ventes du jour")
        layout.addLayout(cards)

        control_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Recherche rapide: nom / code-barres / référence / marque")
        self.search_input.returnPressed.connect(self._search_products)
        self.search_input.textChanged.connect(self._search_products)
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

        self.search_table = QTableWidget(0, 7)
        self.search_table.setHorizontalHeaderLabels(["ID", "Barcode", "Réf", "Nom", "Marque", "Prix", "Stock"])
        layout.addWidget(self.search_table)

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

    def _build_products_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("Gestion produits")
        header.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(header)

        actions = QHBoxLayout()
        self.products_search_input = QLineEdit()
        self.products_search_input.setPlaceholderText("Rechercher produit")
        self.products_search_input.textChanged.connect(self._refresh_products_table)

        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._create_product)
        btn_delete = QPushButton("Supprimer")
        btn_delete.clicked.connect(self._delete_selected_product)
        btn_toggle = QPushButton("Activer / Désactiver")
        btn_toggle.clicked.connect(self._toggle_selected_product_status)

        actions.addWidget(self.products_search_input, 1)
        actions.addWidget(btn_add)
        actions.addWidget(btn_toggle)
        actions.addWidget(btn_delete)
        layout.addLayout(actions)

        self.products_table = QTableWidget(0, 9)
        self.products_table.setHorizontalHeaderLabels(
            ["ID", "Barcode", "Réf", "Nom", "Marque", "Prix vente", "Stock", "Stock min", "Statut"]
        )
        layout.addWidget(self.products_table)
        return page

    def _build_stock_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("Gestion stock")
        header.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(header)

        row = QHBoxLayout()
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Rechercher produit pour stock")
        self.stock_search_input.textChanged.connect(self._refresh_stock_table)

        restock_btn = QPushButton("Renouveler stock")
        restock_btn.clicked.connect(self._restock_selected_product)
        set_stock_btn = QPushButton("Mettre stock exact")
        set_stock_btn.clicked.connect(self._set_selected_stock)

        row.addWidget(self.stock_search_input, 1)
        row.addWidget(restock_btn)
        row.addWidget(set_stock_btn)
        layout.addLayout(row)

        self.stock_table = QTableWidget(0, 8)
        self.stock_table.setHorizontalHeaderLabels(
            ["ID", "Barcode", "Nom", "Stock", "Min", "Max", "Unité", "Alerte"]
        )
        layout.addWidget(self.stock_table)
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
        if row == 1:
            self._refresh_products_table()
        if row == 4:
            self._refresh_stock_table()

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
            self.search_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.search_table.setItem(row, 1, QTableWidgetItem(p.barcode))
            self.search_table.setItem(row, 2, QTableWidgetItem(p.internal_reference or "-"))
            self.search_table.setItem(row, 3, QTableWidgetItem(p.name))
            self.search_table.setItem(row, 4, QTableWidgetItem(p.brand or "-"))
            self.search_table.setItem(row, 5, QTableWidgetItem(str(p.sale_price)))
            self.search_table.setItem(row, 6, QTableWidgetItem(str(p.stock_quantity)))

    def _load_notifications(self) -> None:
        with SessionLocal() as session:
            product_repo = ProductRepository(session)
            low_stock = product_repo.count_low_stock()
            notifications: list[str] = []
            if low_stock > 0:
                notifications.append(f"⚠ {low_stock} produit(s) en rupture ou sous stock minimum.")
            else:
                notifications.append("✅ Stock sous contrôle.")
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
        self.activity_box.setPlainText("\n".join(msg for msg, _ in entries[:12]) or "Aucune activité récente.")

    def _search_products(self) -> None:
        query = self.search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query) if query else repo.list_all()[:20]
        self._fill_search_results(products)

    def _refresh_products_table(self) -> None:
        query = self.products_search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query, limit=200) if query else repo.list_all()

        self.products_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.products_table.setItem(row, 1, QTableWidgetItem(p.barcode))
            self.products_table.setItem(row, 2, QTableWidgetItem(p.internal_reference or "-"))
            self.products_table.setItem(row, 3, QTableWidgetItem(p.name))
            self.products_table.setItem(row, 4, QTableWidgetItem(p.brand or "-"))
            self.products_table.setItem(row, 5, QTableWidgetItem(str(p.sale_price)))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(p.stock_quantity)))
            self.products_table.setItem(row, 7, QTableWidgetItem(str(p.stock_min)))
            self.products_table.setItem(row, 8, QTableWidgetItem(p.status.value))

    def _refresh_stock_table(self) -> None:
        query = self.stock_search_input.text().strip()
        with SessionLocal() as session:
            repo = ProductRepository(session)
            products = repo.search_by_name_or_barcode(query, limit=200) if query else repo.list_all()

        self.stock_table.setRowCount(len(products))
        for row, p in enumerate(products):
            alert = "RUPTURE" if p.stock_quantity <= 0 else ("ALERTE" if p.stock_quantity <= p.stock_min else "OK")
            self.stock_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.stock_table.setItem(row, 1, QTableWidgetItem(p.barcode))
            self.stock_table.setItem(row, 2, QTableWidgetItem(p.name))
            self.stock_table.setItem(row, 3, QTableWidgetItem(str(p.stock_quantity)))
            self.stock_table.setItem(row, 4, QTableWidgetItem(str(p.stock_min)))
            self.stock_table.setItem(row, 5, QTableWidgetItem(str(p.stock_max)))
            self.stock_table.setItem(row, 6, QTableWidgetItem(p.unit))
            self.stock_table.setItem(row, 7, QTableWidgetItem(alert))

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

        expiration_qdate = dialog.expiration_input.date()
        expiration_date = date(expiration_qdate.year(), expiration_qdate.month(), expiration_qdate.day())

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

        promo_type: PromotionType = dialog.type_box.currentData()
        value_text = dialog.value_input.text().strip()
        if not value_text:
            QMessageBox.warning(self, "Erreur", "Valeur de promotion requise")
            return

        try:
            discount_value = Decimal(value_text)
        except InvalidOperation:
            QMessageBox.warning(self, "Erreur", "Valeur de promotion invalide")
            return

        with SessionLocal() as session:
            repo = PromotionRepository(session)
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

    def _delete_selected_product(self) -> None:
        product_id = self._selected_product_id_from_table(self.products_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Sélectionnez un produit à supprimer.")
            return

        if QMessageBox.question(self, "Confirmation", "Supprimer ce produit ?") != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            repo = ProductRepository(session)
            ok = repo.delete(product_id)
            if ok:
                session.commit()
            else:
                session.rollback()
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
        self.refresh_dashboard()

    def _toggle_selected_product_status(self) -> None:
        product_id = self._selected_product_id_from_table(self.products_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Sélectionnez un produit.")
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

    def _restock_selected_product(self) -> None:
        product_id = self._selected_product_id_from_table(self.stock_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Sélectionnez un produit.")
            return

        qty, ok = QInputDialog.getInt(self, "Renouvellement de stock", "Quantité à ajouter", 1, 1, 1_000_000)
        if not ok:
            return

        with SessionLocal() as session:
            repo = ProductRepository(session)
            if not repo.restock(product_id, qty):
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            session.commit()

        self.refresh_dashboard()

    def _set_selected_stock(self) -> None:
        product_id = self._selected_product_id_from_table(self.stock_table)
        if not product_id:
            QMessageBox.information(self, "Information", "Sélectionnez un produit.")
            return

        qty, ok = QInputDialog.getInt(self, "Mise à jour stock", "Nouveau stock", 0, 0, 1_000_000)
        if not ok:
            return

        with SessionLocal() as session:
            repo = ProductRepository(session)
            if not repo.update_stock(product_id, qty):
                QMessageBox.warning(self, "Erreur", "Produit introuvable")
                return
            session.commit()

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
        self._refresh_products_table()
        self._refresh_stock_table()
