from __future__ import annotations

from core.security import hash_password, verify_password
from models.user import User, UserRole
from repositories.user_repo import UserRepository


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole,
        nom: str,
        prenom: str,
        employee_code: str,
        telephone: str | None = None,
    ) -> User:
        existing = self.repo.get_by_username(username)
        if existing:
            raise ValueError("Username already exists")

        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            nom=nom,
            prenom=prenom,
            employee_code=employee_code,
            telephone=telephone,
        )
        return self.repo.add(user)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
