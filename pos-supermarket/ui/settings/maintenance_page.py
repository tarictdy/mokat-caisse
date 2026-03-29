from __future__ import annotations

import platform
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import text

from core.app_config import APP_VERSION, BACKUP_PATH, BASE_DIR, DB_PATH
from core.database import SessionLocal
from models.maintenance import MaintenanceRole
from repositories.maintenance_repo import MaintenanceRepository
from services.maintenance_service import MaintenanceService


class MaintenanceAuthDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Acces maintenance securise")
        self.setModal(True)
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.username_input = QLineEdit("socaf")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Identifiant", self.username_input)
        layout.addRow("Mot de passe", self.password_input)
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        ok_btn = QPushButton("Valider")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)
        layout.addRow(buttons)


class MaintenancePage(QWidget):
    def __init__(self, current_user: str) -> None:
        super().__init__()
        self.current_user = current_user
        self._authenticated = False
        self._build_ui()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._authenticated:
            self._request_access()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Parametres / Maintenance securisee")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.system_tab = self._build_system_tab()
        self.modules_tab = self._build_modules_tab()
        self.flows_tab = self._build_flows_tab()
        self.files_tab = self._build_files_tab()
        self.db_tab = self._build_db_tab()
        self.logs_tab = self._build_logs_tab()
        self.security_tab = self._build_security_tab()

        self.tabs.addTab(self.system_tab, "Vue systeme")
        self.tabs.addTab(self.modules_tab, "Modules")
        self.tabs.addTab(self.flows_tab, "Flux")
        self.tabs.addTab(self.files_tab, "Fichiers critiques")
        self.tabs.addTab(self.db_tab, "Base de donnees")
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.addTab(self.security_tab, "Securite maintenance")

    def _request_access(self) -> None:
        dialog = MaintenanceAuthDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.tabs.setEnabled(False)
            return
        with SessionLocal() as session:
            repo = MaintenanceRepository(session)
            service = MaintenanceService(repo)
            ok, message = service.authenticate(dialog.username_input.text().strip(), dialog.password_input.text())
            session.commit()
        if not ok:
            QMessageBox.warning(self, "Acces refuse", message)
            self.tabs.setEnabled(False)
            return
        self._authenticated = True
        self.tabs.setEnabled(True)
        self.refresh_data()

    def refresh_data(self) -> None:
        self._load_system_info()
        self._load_files_info()
        self._load_db_info()
        self._load_logs()
        self._load_security_info()

    def _build_system_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        layout.addWidget(self.system_info)
        return tab

    def _build_modules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Module", "Statut", "Service principal", "Dependances"])
        modules = [
            ("Authentification", "Charge", "UserService", "UserRepository -> SQLite"),
            ("Dashboard Admin", "Charge", "FinanceReportService", "Sale/Charge repos"),
            ("Dashboard Supervisor", "Charge", "-", "UI"),
            ("Dashboard Cashier", "Charge", "SaleService", "Product/Sale repos"),
            ("POS / Caisse", "Charge", "SaleService", "PaymentService, PrinterService"),
            ("Produits", "Charge", "ProductService", "ProductRepository"),
            ("Stock", "Charge", "StockService", "ProductRepository"),
            ("Promotions", "Charge", "PromotionService", "PromotionRepository"),
            ("Utilisateurs", "Charge", "UserService", "UserRepository"),
            ("Rapports", "Charge", "FinanceReportService", "Sale + Charge"),
            ("Maintenance", "Charge", "MaintenanceService", "MaintenanceRepository"),
        ]
        table.setRowCount(len(modules))
        for row, values in enumerate(modules):
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table)
        return tab

    def _build_flows_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(
            "LoginWindow -> UserService -> UserRepository -> SQLite\n"
            "AdminDashboard -> FinanceReportService -> SaleRepository/ChargeRepository -> SQLite\n"
            "POSScreen -> SaleService -> ProductRepository/SaleRepository -> SQLite\n"
            "POSScreen -> PaymentService -> PrinterService -> hardware\n"
            "MaintenancePage -> MaintenanceService -> MaintenanceRepository -> SQLite"
        )
        layout.addWidget(txt)
        return tab

    def _build_files_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.files_table = QTableWidget(0, 6)
        self.files_table.setHorizontalHeaderLabels(["Nom", "Chemin", "Existe", "Taille", "Derniere modif", "Acces"])
        layout.addWidget(self.files_table)
        return tab

    def _build_db_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.db_summary = QTextEdit()
        self.db_summary.setReadOnly(True)
        self.db_tables = QTableWidget(0, 2)
        self.db_tables.setHorizontalHeaderLabels(["Table", "Nombre lignes"])
        layout.addWidget(self.db_summary)
        layout.addWidget(self.db_tables)
        return tab

    def _build_logs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        filters = QHBoxLayout()
        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["TOUS", "INFO", "WARNING", "ERROR", "CRITICAL", "SECURITY"])
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("Rechercher dans les logs...")
        refresh = QPushButton("Actualiser")
        refresh.clicked.connect(self._load_logs)
        filters.addWidget(self.log_level_filter)
        filters.addWidget(self.log_search_input, 1)
        filters.addWidget(refresh)
        self.log_level_filter.currentIndexChanged.connect(self._load_logs)
        self.log_search_input.textChanged.connect(self._load_logs)
        layout.addLayout(filters)
        self.logs_output = QTextEdit()
        self.logs_output.setReadOnly(True)
        layout.addWidget(self.logs_output)
        return tab

    def _build_security_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        actions = QHBoxLayout()
        add_btn = QPushButton("+ Ajouter acces")
        add_btn.clicked.connect(self._create_access)
        disable_btn = QPushButton("Activer/Desactiver")
        disable_btn.clicked.connect(self._toggle_access_status)
        change_btn = QPushButton("Changer mot de passe")
        change_btn.clicked.connect(self._change_access_password)
        actions.addWidget(add_btn)
        actions.addWidget(disable_btn)
        actions.addWidget(change_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.security_table = QTableWidget(0, 6)
        self.security_table.setHorizontalHeaderLabels(["Username", "Role", "Actif", "Cree le", "Dernier acces", "Tentatives"])
        layout.addWidget(self.security_table, 1)
        return tab

    def _load_system_info(self) -> None:
        info = [
            f"Version app: {APP_VERSION}",
            f"Python: {sys.version.split()[0]}",
            f"OS: {platform.platform()}",
            f"Date systeme: {datetime.now().isoformat(sep=' ', timespec='seconds')}",
            f"Utilisateur connecte: {self.current_user}",
            f"Dossier base: {BASE_DIR}",
        ]
        self.system_info.setPlainText("\n".join(info))

    def _load_files_info(self) -> None:
        candidates = [
            ("Base SQLite", DB_PATH),
            ("Backup DB", BACKUP_PATH),
            ("Style QSS", BASE_DIR / "assets" / "styles" / "app.qss"),
            ("Splash branding PNG", BASE_DIR.parent / "splash_branding.png"),
            ("Splash branding JPG", BASE_DIR.parent / "splash_branding.jpg"),
            ("Maintenance log", BASE_DIR / "data" / "maintenance.log"),
        ]
        self.files_table.setRowCount(len(candidates))
        for row, (name, path) in enumerate(candidates):
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat(sep=" ", timespec="seconds") if exists else "-"
            values = [name, str(path), "Oui" if exists else "Non", str(size), mtime, "OK" if exists and path.is_file() else "N/A"]
            for col, value in enumerate(values):
                self.files_table.setItem(row, col, QTableWidgetItem(value))

    def _load_db_info(self) -> None:
        with SessionLocal() as session:
            conn = session.connection()
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
            tracked = ["users", "products", "sales", "sale_items", "stock_movements", "promotions", "charges", "maintenance_accesses", "maintenance_audit_logs"]
            counts: list[tuple[str, int]] = []
            for table_name in tracked:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()
                    counts.append((table_name, int(count)))
                except Exception:
                    counts.append((table_name, 0))
        db_exists = DB_PATH.exists()
        db_size = DB_PATH.stat().st_size if db_exists else 0
        db_mtime = datetime.fromtimestamp(DB_PATH.stat().st_mtime).isoformat(sep=" ", timespec="seconds") if db_exists else "-"
        summary = [
            f"Chemin DB: {DB_PATH}",
            f"DB existe: {'Oui' if db_exists else 'Non'}",
            f"Taille DB: {db_size} octets",
            f"Derniere modification: {db_mtime}",
            f"Tables detectees: {len(tables)}",
            f"Etat backup: {'present' if BACKUP_PATH.exists() else 'absent'}",
        ]
        self.db_summary.setPlainText("\n".join(summary))
        self.db_tables.setRowCount(len(counts))
        for row, (name, count) in enumerate(counts):
            self.db_tables.setItem(row, 0, QTableWidgetItem(name))
            self.db_tables.setItem(row, 1, QTableWidgetItem(str(count)))

    def _load_logs(self) -> None:
        with SessionLocal() as session:
            repo = MaintenanceRepository(session)
            audit_logs = repo.list_audits(limit=300)
        level_filter = self.log_level_filter.currentText()
        keyword = self.log_search_input.text().strip().lower()
        lines = []
        for log in audit_logs:
            if level_filter != "TOUS" and log.level.upper() != level_filter:
                continue
            line = f"[{log.created_at:%Y-%m-%d %H:%M:%S}] [{log.level}] {log.event_type} - {log.message} ({log.actor or '-'})"
            if keyword and keyword not in line.lower():
                continue
            lines.append(line)
        self.logs_output.setPlainText("\n".join(lines) if lines else "Aucun log correspondant.")

    def _load_security_info(self) -> None:
        with SessionLocal() as session:
            accesses = MaintenanceRepository(session).list_accesses()
        self.security_table.setRowCount(len(accesses))
        for row, access in enumerate(accesses):
            values = [
                access.username,
                access.role.value,
                "Oui" if access.is_active else "Non",
                access.created_at.strftime("%Y-%m-%d %H:%M"),
                access.last_access_at.strftime("%Y-%m-%d %H:%M") if access.last_access_at else "-",
                str(access.failed_attempts),
            ]
            for col, value in enumerate(values):
                self.security_table.setItem(row, col, QTableWidgetItem(value))

    def _selected_access_username(self) -> str | None:
        row = self.security_table.currentRow()
        if row < 0:
            return None
        item = self.security_table.item(row, 0)
        return item.text() if item else None

    def _create_access(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau compte maintenance")
        form = QFormLayout(dialog)
        user_input = QLineEdit()
        pass_input = QLineEdit()
        pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        role_box = QComboBox()
        role_box.addItem("Support", MaintenanceRole.SUPPORT)
        role_box.addItem("Admin", MaintenanceRole.ADMIN)
        role_box.addItem("SuperAdmin", MaintenanceRole.SUPERADMIN)
        form.addRow("Identifiant", user_input)
        form.addRow("Mot de passe", pass_input)
        form.addRow("Role", role_box)
        save = QPushButton("Creer")
        save.clicked.connect(dialog.accept)
        form.addRow(save)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        with SessionLocal() as session:
            service = MaintenanceService(MaintenanceRepository(session))
            try:
                service.create_access(user_input.text().strip(), pass_input.text(), role_box.currentData())
                session.commit()
            except ValueError as exc:
                session.rollback()
                QMessageBox.warning(self, "Erreur", str(exc))
                return
        self._load_security_info()
        self._load_logs()

    def _toggle_access_status(self) -> None:
        username = self._selected_access_username()
        if not username:
            QMessageBox.information(self, "Information", "Selectionnez un acces maintenance.")
            return
        with SessionLocal() as session:
            repo = MaintenanceRepository(session)
            access = repo.get_access_by_username(username)
            if not access:
                QMessageBox.warning(self, "Erreur", "Acces introuvable")
                return
            service = MaintenanceService(repo)
            service.set_access_status(username, not access.is_active)
            session.commit()
        self._load_security_info()
        self._load_logs()

    def _change_access_password(self) -> None:
        username = self._selected_access_username()
        if not username:
            QMessageBox.information(self, "Information", "Selectionnez un acces maintenance.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Changer mot de passe maintenance")
        form = QFormLayout(dialog)
        pwd = QLineEdit()
        pwd.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nouveau mot de passe", pwd)
        ok = QPushButton("Valider")
        ok.clicked.connect(dialog.accept)
        form.addRow(ok)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        with SessionLocal() as session:
            service = MaintenanceService(MaintenanceRepository(session))
            try:
                service.change_password(username, pwd.text())
                session.commit()
            except ValueError as exc:
                session.rollback()
                QMessageBox.warning(self, "Erreur", str(exc))
                return
        self._load_logs()
