from __future__ import annotations

import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
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
        self.setWindowTitle("MOKAT MARKET - Connexion")
        self.setMinimumSize(1100, 700)
        self.setObjectName("LoginRoot")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════════════════
        # LEFT PANEL — Branding & Illustration
        # ══════════════════════════════════════════════════════════
        left = QWidget()
        left.setObjectName("LoginRoot")
        left.setMinimumWidth(480)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(60, 60, 60, 60)
        left_layout.setSpacing(0)

        # Logo / Brand
        logo_row = QHBoxLayout()
        logo_row.setSpacing(12)
        
        logo_icon = QLabel()
        logo_icon.setFixedSize(48, 48)
        logo_icon.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);"
            "border-radius: 12px;"
        )
        logo_icon_text = QLabel("M")
        logo_icon_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon_text.setStyleSheet(
            "color: #FFFFFF; font-size: 24px; font-weight: 800;"
            "background: transparent;"
        )
        icon_layout = QVBoxLayout(logo_icon)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(logo_icon_text)
        
        brand_text = QLabel("MOKAT MARKET")
        brand_text.setStyleSheet(
            "color: #FFFFFF; font-size: 22px; font-weight: 800;"
            "letter-spacing: 3px; background: transparent;"
        )
        
        logo_row.addWidget(logo_icon)
        logo_row.addWidget(brand_text)
        logo_row.addStretch()
        left_layout.addLayout(logo_row)
        
        left_layout.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Main headline
        headline = QLabel("Gerez votre\ncommerce en\ntoute simplicite")
        headline.setStyleSheet(
            "color: #FFFFFF; font-size: 42px; font-weight: 700;"
            "line-height: 1.2; background: transparent; letter-spacing: -1px;"
        )
        headline.setWordWrap(True)
        left_layout.addWidget(headline)

        left_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Description
        desc = QLabel(
            "Solution complete de point de vente pour les\n"
            "supermarches et commerces de detail."
        )
        desc.setStyleSheet(
            "color: #94A3B8; font-size: 16px; line-height: 1.6;"
            "background: transparent;"
        )
        desc.setWordWrap(True)
        left_layout.addWidget(desc)

        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Feature badges
        features_row = QHBoxLayout()
        features_row.setSpacing(12)
        
        for feature in ["Ventes", "Stock", "Rapports"]:
            badge = QFrame()
            badge.setStyleSheet(
                "background: #1E293B; border-radius: 20px; padding: 0;"
            )
            badge_layout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(16, 10, 16, 10)
            badge_layout.setSpacing(8)
            
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet("background: #2563EB; border-radius: 4px;")
            
            badge_text = QLabel(feature)
            badge_text.setStyleSheet(
                "color: #E2E8F0; font-size: 13px; font-weight: 600;"
                "background: transparent;"
            )
            
            badge_layout.addWidget(dot)
            badge_layout.addWidget(badge_text)
            features_row.addWidget(badge)
        
        features_row.addStretch()
        left_layout.addLayout(features_row)

        left_layout.addStretch()

        # Footer
        footer = QLabel("v2.0  -  Propulse par SOCAFTDYINDUSTRUAP")
        footer.setStyleSheet(
            "color: #475569; font-size: 12px; background: transparent;"
        )
        left_layout.addWidget(footer)

        # ══════════════════════════════════════════════════════════
        # RIGHT PANEL — Login Form
        # ══════════════════════════════════════════════════════════
        right = QWidget()
        right.setStyleSheet("background: #F8FAFC;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card container with shadow effect
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setFixedWidth(420)
        card.setStyleSheet(
            "QFrame#LoginCard {"
            "    background: #FFFFFF;"
            "    border-radius: 24px;"
            "    border: 1px solid #E2E8F0;"
            "}"
        )
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(Qt.GlobalColor.black)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 48, 40, 48)
        card_layout.setSpacing(0)

        # Welcome text
        welcome_lbl = QLabel("Bienvenue")
        welcome_lbl.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #0F172A;"
            "letter-spacing: -0.5px; background: transparent;"
        )
        card_layout.addWidget(welcome_lbl)

        card_layout.addSpacerItem(QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        sub_lbl = QLabel("Connectez-vous pour acceder a votre espace")
        sub_lbl.setStyleSheet(
            "font-size: 14px; color: #64748B; background: transparent;"
        )
        card_layout.addWidget(sub_lbl)

        card_layout.addSpacerItem(QSpacerItem(20, 36, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Username field
        lbl_user = QLabel("Nom d'utilisateur")
        lbl_user.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #374151;"
            "margin-bottom: 8px; background: transparent;"
        )
        card_layout.addWidget(lbl_user)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Entrez votre identifiant")
        self.username_input.setMinimumHeight(52)
        self.username_input.setStyleSheet(
            "QLineEdit {"
            "    background: #F8FAFC;"
            "    border: 2px solid #E2E8F0;"
            "    border-radius: 12px;"
            "    padding: 14px 18px;"
            "    font-size: 14px;"
            "    color: #0F172A;"
            "}"
            "QLineEdit:hover { border-color: #CBD5E1; }"
            "QLineEdit:focus {"
            "    border-color: #2563EB;"
            "    background: #FFFFFF;"
            "}"
        )
        card_layout.addWidget(self.username_input)

        card_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Password field
        lbl_pass = QLabel("Mot de passe")
        lbl_pass.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #374151;"
            "margin-bottom: 8px; background: transparent;"
        )
        card_layout.addWidget(lbl_pass)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Entrez votre mot de passe")
        self.password_input.setMinimumHeight(52)
        self.password_input.setStyleSheet(
            "QLineEdit {"
            "    background: #F8FAFC;"
            "    border: 2px solid #E2E8F0;"
            "    border-radius: 12px;"
            "    padding: 14px 18px;"
            "    font-size: 14px;"
            "    color: #0F172A;"
            "}"
            "QLineEdit:hover { border-color: #CBD5E1; }"
            "QLineEdit:focus {"
            "    border-color: #2563EB;"
            "    background: #FFFFFF;"
            "}"
        )
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacerItem(QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            "color: #DC2626; font-size: 13px; font-weight: 500;"
            "padding: 10px 14px; background: #FEF2F2;"
            "border-radius: 8px; border: 1px solid #FECACA;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        card_layout.addWidget(self.error_label)

        card_layout.addSpacerItem(QSpacerItem(20, 28, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Login button
        self.login_button = QPushButton("Se connecter")
        self.login_button.setMinimumHeight(54)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet(
            "QPushButton {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);"
            "    color: #FFFFFF;"
            "    border: none;"
            "    border-radius: 12px;"
            "    font-size: 15px;"
            "    font-weight: 700;"
            "}"
            "QPushButton:hover {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #1E40AF);"
            "}"
            "QPushButton:pressed {"
            "    background: #1E40AF;"
            "}"
            "QPushButton:disabled {"
            "    background: #CBD5E1;"
            "    color: #94A3B8;"
            "}"
        )
        self.login_button.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_button)

        card_layout.addSpacerItem(QSpacerItem(20, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Help text
        help_lbl = QLabel("Besoin d'aide ? Contactez votre administrateur")
        help_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_lbl.setStyleSheet(
            "font-size: 12px; color: #94A3B8; background: transparent;"
        )
        card_layout.addWidget(help_lbl)

        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add panels
        root.addWidget(left, 5)
        root.addWidget(right, 5)

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
                    self.error_label.setText("Identifiants incorrects. Verifiez votre nom d'utilisateur et mot de passe.")
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

        except Exception as exc:
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
