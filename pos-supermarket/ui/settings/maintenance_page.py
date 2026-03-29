from __future__ import annotations

import platform
import sys
from datetime import datetime
import importlib.util
from pathlib import Path

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from sqlalchemy import text

from core.app_config import APP_VERSION, BACKUP_PATH, BASE_DIR, DB_PATH
from core.database import SessionLocal
from models.maintenance import MaintenanceAudit
from models.maintenance import MaintenanceRole
from repositories.maintenance_repo import MaintenanceRepository
from services.firebase_backup_service import FirebaseBackupService
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
        self.firebase_backup_service = FirebaseBackupService()
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
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
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

        refresh_all = QPushButton("Actualiser la console maintenance")
        refresh_all.setStyleSheet("QPushButton { background: #0EA5E9; color: white; border-radius: 8px; padding: 10px 14px; }")
        refresh_all.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_all, alignment=Qt.AlignmentFlag.AlignRight)

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
        self._load_firebase_status()

    def _build_system_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        firebase_card = QFrame()
        firebase_layout = QVBoxLayout(firebase_card)
        firebase_title = QLabel("Sauvegarde cloud Firebase")
        firebase_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        firebase_layout.addWidget(firebase_title)

        self.firebase_status_label = QLabel("Statut Firebase: -")
        self.firebase_target_label = QLabel("Projet/Bucket: -")
        self.firebase_last_sync_label = QLabel("Dernier envoi: -")
        self.firebase_result_label = QLabel("Resultat: -")
        for widget in (
            self.firebase_status_label,
            self.firebase_target_label,
            self.firebase_last_sync_label,
            self.firebase_result_label,
        ):
            widget.setStyleSheet("color: #334155; font-size: 12px;")
            firebase_layout.addWidget(widget)

        send_btn = QPushButton("Envoyer la base vers Firebase")
        send_btn.setStyleSheet("QPushButton { background: #2563EB; color: white; border-radius: 8px; padding: 10px 14px; }")
        send_btn.clicked.connect(self._send_db_to_firebase)
        firebase_layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(firebase_card)

        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        layout.addWidget(self.system_info)
        return tab

    def _build_modules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Module", "Statut", "Service principal", "Dependances"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(table)
        modules = [
            ("Authentification", "ui.login.login_window", "UserService", "UserRepository -> SQLite"),
            ("Dashboard Admin", "ui.dashboard.admin_dashboard", "FinanceReportService", "Sale/Charge repos"),
            ("Dashboard Supervisor", "ui.dashboard.supervisor_dashboard", "-", "UI"),
            ("Dashboard Cashier", "ui.dashboard.cashier_dashboard", "SaleService", "Product/Sale repos"),
            ("POS / Caisse", "ui.sales.pos_screen", "SaleService", "PaymentService, PrinterService"),
            ("Produits", "services.product_service", "ProductService", "ProductRepository"),
            ("Stock", "services.stock_service", "StockService", "ProductRepository"),
            ("Promotions", "services.promotion_service", "PromotionService", "PromotionRepository"),
            ("Utilisateurs", "services.user_service", "UserService", "UserRepository"),
            ("Rapports", "services.finance_report_service", "FinanceReportService", "Sale + Charge"),
            ("Maintenance", "ui.settings.maintenance_page", "MaintenanceService", "MaintenanceRepository"),
        ]
        table.setRowCount(len(modules))
        for row, (label, module_path, service, deps) in enumerate(modules):
            status = "Charge" if importlib.util.find_spec(module_path) else "Manquant"
            values = (label, status, service, deps)
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(table)
        return tab

    def _build_flows_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.flow_table = QTableWidget(0, 5)
        self.flow_table.setHorizontalHeaderLabels(["UI Source", "Service", "Repository", "Base/Infra", "But"])
        self.flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(self.flow_table)
        flow_rows = [
            ("LoginWindow", "UserService", "UserRepository", "SQLite", "Authentification utilisateur"),
            ("POSScreen", "SaleService", "SaleRepository/ProductRepository", "SQLite", "Encaissement + stock"),
            ("POSScreen", "PaymentService", "-", "Printer/CashDrawer", "Paiement + impression"),
            ("AdminDashboard", "FinanceReportService", "Sale/Charge repositories", "SQLite", "Analyse rentabilite"),
            ("MaintenancePage", "MaintenanceService", "MaintenanceRepository", "SQLite", "Securite maintenance"),
            ("MaintenancePage", "FirebaseBackupService", "-", "Firebase Storage", "Backup cloud manuel"),
        ]
        self.flow_table.setRowCount(len(flow_rows))
        for row, values in enumerate(flow_rows):
            for col, value in enumerate(values):
                self.flow_table.setItem(row, col, QTableWidgetItem(value))
        layout.addWidget(self.flow_table)
        return tab

    def _build_files_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.files_table = QTableWidget(0, 6)
        self.files_table.setHorizontalHeaderLabels(["Nom", "Chemin", "Existe", "Taille", "Derniere modif", "Acces"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(self.files_table)
        layout.addWidget(self.files_table)
        return tab

    def _build_db_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.db_summary = QTextEdit()
        self.db_summary.setReadOnly(True)
        self.db_tables = QTableWidget(0, 2)
        self.db_tables.setHorizontalHeaderLabels(["Table", "Nombre lignes"])
        self.db_tables.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(self.db_tables)
        layout.addWidget(self.db_summary)
        layout.addWidget(self.db_tables)
        return tab

    def _build_logs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        filters = QHBoxLayout()
        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["TOUS", "INFO", "WARNING", "ERROR", "CRITICAL", "SECURITY"])
        self.log_start_date = QDateEdit()
        self.log_start_date.setCalendarPopup(True)
        self.log_start_date.setDate(QDate.currentDate().addDays(-30))
        self.log_end_date = QDateEdit()
        self.log_end_date.setCalendarPopup(True)
        self.log_end_date.setDate(QDate.currentDate())
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("Rechercher dans les logs...")
        refresh = QPushButton("Actualiser")
        refresh.clicked.connect(self._load_logs)
        filters.addWidget(self.log_level_filter)
        filters.addWidget(self.log_start_date)
        filters.addWidget(self.log_end_date)
        filters.addWidget(self.log_search_input, 1)
        filters.addWidget(refresh)
        self.log_level_filter.currentIndexChanged.connect(self._load_logs)
        self.log_start_date.dateChanged.connect(self._load_logs)
        self.log_end_date.dateChanged.connect(self._load_logs)
        self.log_search_input.textChanged.connect(self._load_logs)
        layout.addLayout(filters)
        self.logs_output = QTextEdit()
        self.logs_output.setReadOnly(True)
        self.logs_output.setMinimumHeight(320)
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
        self.security_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(self.security_table)

        self.firebase_history_table = QTableWidget(0, 5)
        self.firebase_history_table.setHorizontalHeaderLabels(["Date", "Niveau", "Evenement", "Message", "Acteur"])
        self.firebase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._configure_table(self.firebase_history_table)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.security_table)
        splitter.addWidget(self.firebase_history_table)
        splitter.setSizes([280, 260])
        layout.addWidget(splitter, 1)
        return tab

    def _configure_table(self, table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(False)

    def _load_system_info(self) -> None:
        info = [
            f"Version app: {APP_VERSION}",
            f"Python: {sys.version.split()[0]}",
            f"OS: {platform.platform()}",
            f"Date systeme: {datetime.now().isoformat(sep=' ', timespec='seconds')}",
            f"Utilisateur connecte: {self.current_user}",
            f"Dossier base: {BASE_DIR}",
            f"Machine: {platform.node()}",
            f"Architecture: {platform.machine()}",
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
            ("Dossier data", BASE_DIR / "data"),
            ("Dossier exports", BASE_DIR / "exports"),
            ("Credentials Firebase", BASE_DIR.parent / "ts" / "firebase-service-account.json"),
        ]
        self.files_table.setRowCount(len(candidates))
        for row, (name, path) in enumerate(candidates):
            exists = path.exists()
            size = path.stat().st_size if exists and path.is_file() else 0
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat(sep=" ", timespec="seconds") if exists else "-"
            values = [name, str(path), "Oui" if exists else "Non", str(size), mtime, "OK" if exists else "N/A"]
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
        start = self.log_start_date.date().toPyDate()
        end = self.log_end_date.date().toPyDate()
        lines = []
        for log in audit_logs:
            if level_filter != "TOUS" and log.level.upper() != level_filter:
                continue
            created_day = log.created_at.date()
            if created_day < start or created_day > end:
                continue
            line = f"[{log.created_at:%Y-%m-%d %H:%M:%S}] [{log.level}] {log.event_type} - {log.message} ({log.actor or '-'})"
            if keyword and keyword not in line.lower():
                continue
            lines.append(line)
        self.logs_output.setPlainText("\n".join(lines) if lines else "Aucun log correspondant.")
        self._load_firebase_history(audit_logs)

    def _load_firebase_history(self, audit_logs: list[MaintenanceAudit]) -> None:
        firebase_events = [log for log in audit_logs if log.event_type.startswith("firebase_")]
        self.firebase_history_table.setRowCount(len(firebase_events))
        for row, log in enumerate(firebase_events):
            values = [
                log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                log.level,
                log.event_type,
                log.message,
                log.actor or "-",
            ]
            for col, value in enumerate(values):
                self.firebase_history_table.setItem(row, col, QTableWidgetItem(value))

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

    def _load_firebase_status(self) -> None:
        status = self.firebase_backup_service.config_status()
        self.firebase_status_label.setText(
            f"Statut Firebase Admin SDK: {'Pret' if status['sdk_available'] == 'oui' else 'Indisponible'}"
        )
        self.firebase_target_label.setText(
            f"Credentials: {status['credentials_path']} | Bucket: {status['bucket']}"
        )

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

    def _send_db_to_firebase(self) -> None:
        self.firebase_result_label.setText("Resultat: en cours d'envoi...")
        self.firebase_result_label.setStyleSheet("color: #1D4ED8; font-size: 12px;")
        result = self.firebase_backup_service.upload_backup()

        with SessionLocal() as session:
            repo = MaintenanceRepository(session)
            level = "INFO" if result.success else "ERROR"
            event_type = "firebase_backup_success" if result.success else "firebase_backup_failure"
            detail = result.message
            if result.success:
                detail = f"{result.message} objet={result.object_path} taille={result.file_size or 0}"
            repo.add_audit(
                MaintenanceAudit(
                    level=level,
                    event_type=event_type,
                    message=detail,
                    actor=self.current_user,
                )
            )
            session.commit()

        if result.success:
            self.firebase_last_sync_label.setText(
                f"Dernier envoi: {result.sent_at.strftime('%Y-%m-%d %H:%M:%S') if result.sent_at else '-'}"
            )
            self.firebase_result_label.setText(f"Resultat: succes ({result.file_size or 0} octets)")
            self.firebase_result_label.setStyleSheet("color: #15803D; font-size: 12px;")
        else:
            self.firebase_result_label.setText(f"Resultat: echec - {result.message}")
            self.firebase_result_label.setStyleSheet("color: #B91C1C; font-size: 12px;")
        self._load_logs()
