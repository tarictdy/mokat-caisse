from __future__ import annotations

import traceback

from PyQt6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
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
        self.setWindowTitle("Connexion")
        self.setMinimumWidth(380)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Se connecter")
        self.login_button.clicked.connect(self._on_login)

        form = QFormLayout()
        form.addRow("Nom utilisateur", self.username_input)
        form.addRow("Mot de passe", self.password_input)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(self.login_button)

        self._dashboard = None

    def _on_login(self) -> None:
        try:
            with SessionLocal() as session:
                service = UserService(UserRepository(session))
                user = service.authenticate(self.username_input.text().strip(), self.password_input.text())

                if not user:
                    QMessageBox.warning(self, "Erreur", "Identifiants invalides")
                    return

                if user.role == UserRole.ADMIN:
                    self._dashboard = AdminDashboard(user)
                elif user.role == UserRole.SUPERVISOR:
                    self._dashboard = SupervisorDashboard(user)
                else:
                    self._dashboard = CashierDashboard(user)

                self._dashboard.show()
                self.close()
        except Exception as exc:  # pragma: no cover - UI guard
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erreur critique",
                "Impossible d'ouvrir le dashboard.\n"
                f"Détail: {exc}\n"
                "Vérifiez la version Python (3.12 recommandée) et la base locale.",
            )
