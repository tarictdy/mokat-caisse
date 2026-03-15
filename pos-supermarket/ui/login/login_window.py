from __future__ import annotations

import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.database import SessionLocal
from models.user import UserRole
from repositories.user_repo import UserRepository
from services.user_service import UserService
from ui.dashboard.admin_dashboard import AdminDashboard
from ui.dashboard.cashier_dashboard import CashierDashboard
from ui.dashboard.supervisor_dashboard import SupervisorDashboard


class LoginWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MOKAT MARKET — Connexion")
        self.setMinimumSize(960, 600)
        self.setObjectName("LoginRoot")

        # ── Two-column layout ──────────────────────────────
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left branding panel
        left = QWidget()
        left.setObjectName("LoginRoot")
        left.setMinimumWidth(400)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(52, 52, 52, 52)
        left_layout.setSpacing(0)

        brand = QLabel("MOKAT MARKET")
        brand.setStyleSheet(
            "color: #2563EB; font-size: 22px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;"
        )
        tagline = QLabel("Point de Vente Professionnel")
        tagline.setStyleSheet(
            "color: #94A3B8; font-size: 14px; background: transparent; margin-top: 4px;"
        )

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #1E293B; margin: 28px 0;")

        desc = QLabel(
            "Gerez vos ventes, votre stock\net vos promotions depuis\nune seule interface."
        )
        desc.setStyleSheet(
            "color: #CBD5E1; font-size: 15px; line-height: 1.6;"
            "background: transparent;"
        )
        desc.setWordWrap(True)

        left_layout.addStretch()
        left_layout.addWidget(brand)
        left_layout.addWidget(tagline)
        left_layout.addWidget(divider)
        left_layout.addWidget(desc)
        left_layout.addStretch()

        version = QLabel("v1.0 — Powered by SOCAFTDYINDUSTRUAP")
        version.setStyleSheet("color: #334155; font-size: 11px; background: transparent;")
        left_layout.addWidget(version)

        # Right login card panel
        right = QWidget()
        right.setStyleSheet("background: #F8FAFC;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(60, 0, 60, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMinimumWidth(360)
        card.setMaximumWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(32, 32, 32, 32)

        # Title inside card
        title = QLabel("Connexion")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        subtitle = QLabel("Entrez vos identifiants pour continuer")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B; margin-top: -8px;")
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0;")
        card_layout.addWidget(sep)

        # Username
        lbl_user = QLabel("Nom d'utilisateur")
        lbl_user.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ex: admin")
        self.username_input.setMinimumHeight(40)

        # Password
        lbl_pass = QLabel("Mot de passe")
        lbl_pass.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._on_login)

        card_layout.addWidget(lbl_user)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(lbl_pass)
        card_layout.addWidget(self.password_input)

        # Error label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setObjectName("StatusError")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        card_layout.addWidget(self.error_label)

        # Login button
        self.login_button = QPushButton("Se connecter")
        self.login_button.setObjectName("PrimaryLarge")
        self.login_button.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_button)

        right_layout.addStretch()
        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch()

        root.addWidget(left, 2)
        root.addWidget(right, 3)

        self._dashboard = None

    def _on_login(self) -> None:
        self.error_label.setVisible(False)
        self.login_button.setEnabled(False)
        self.login_button.setText("Connexion en cours...")

        try:
            with SessionLocal() as session:
                service = UserService(UserRepository(session))
                user = service.authenticate(
                    self.username_input.text().strip(),
                    self.password_input.text(),
                )

                if not user:
                    self.error_label.setText("Identifiants invalides. Veuillez reessayer.")
                    self.error_label.setVisible(True)
                    self.login_button.setEnabled(True)
                    self.login_button.setText("Se connecter")
                    return

                if user.role == UserRole.ADMIN:
                    self._dashboard = AdminDashboard(user)
                elif user.role == UserRole.SUPERVISOR:
                    self._dashboard = SupervisorDashboard(user)
                else:
                    self._dashboard = CashierDashboard(user)

                self._dashboard.show()
                self.close()

        except Exception as exc:  # pragma: no cover
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erreur critique",
                "Impossible d'ouvrir le dashboard.\n"
                f"Detail: {exc}\n"
                "Verifiez la version Python (3.12 recommandee) et la base locale.",
            )
            self.login_button.setEnabled(True)
            self.login_button.setText("Se connecter")
