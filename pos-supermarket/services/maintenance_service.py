from __future__ import annotations

from datetime import datetime, timedelta

from core.security import hash_password, verify_password
from models.maintenance import MaintenanceAccess, MaintenanceAudit, MaintenanceRole
from repositories.maintenance_repo import MaintenanceRepository


class MaintenanceService:
    MAX_ATTEMPTS = 5
    LOCK_MINUTES = 10

    def __init__(self, repo: MaintenanceRepository) -> None:
        self.repo = repo

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        access = self.repo.get_access_by_username(username)
        if not access:
            self._audit("SECURITY", "maintenance_login_failed", f"Tentative sur utilisateur inconnu: {username}", username)
            return False, "Identifiants invalides"
        if not access.is_active:
            self._audit("SECURITY", "maintenance_login_inactive", "Compte maintenance desactive", username)
            return False, "Acces desactive"
        if access.locked_until and access.locked_until > datetime.utcnow():
            return False, "Compte temporairement verrouille"
        if not verify_password(password, access.password_hash):
            access.failed_attempts += 1
            if access.failed_attempts >= self.MAX_ATTEMPTS:
                access.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCK_MINUTES)
            self._audit("SECURITY", "maintenance_login_failed", "Mot de passe incorrect", username)
            return False, "Identifiants invalides"

        access.failed_attempts = 0
        access.locked_until = None
        access.last_access_at = datetime.utcnow()
        self._audit("SECURITY", "maintenance_login_success", "Connexion maintenance validee", username)
        return True, "OK"

    def create_access(self, username: str, password: str, role: MaintenanceRole) -> MaintenanceAccess:
        existing = self.repo.get_access_by_username(username)
        if existing:
            raise ValueError("Identifiant maintenance deja existant")
        access = MaintenanceAccess(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        self.repo.add_access(access)
        self._audit("SECURITY", "maintenance_access_created", f"Nouveau compte maintenance: {username}", username)
        return access

    def set_access_status(self, username: str, is_active: bool) -> None:
        access = self.repo.get_access_by_username(username)
        if not access:
            raise ValueError("Compte maintenance introuvable")
        access.is_active = is_active
        self._audit(
            "SECURITY",
            "maintenance_access_status",
            f"Compte {username} {'active' if is_active else 'desactive'}",
            username,
        )

    def change_password(self, username: str, new_password: str) -> None:
        access = self.repo.get_access_by_username(username)
        if not access:
            raise ValueError("Compte maintenance introuvable")
        access.password_hash = hash_password(new_password)
        self._audit("SECURITY", "maintenance_password_changed", "Mot de passe maintenance modifie", username)

    def _audit(self, level: str, event_type: str, message: str, actor: str | None = None) -> None:
        self.repo.add_audit(
            MaintenanceAudit(level=level, event_type=event_type, message=message, actor=actor)
        )
