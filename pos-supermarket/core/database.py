from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.app_config import (
    DB_PATH,
    DEFAULT_ADMIN_EMPLOYEE_CODE,
    DEFAULT_ADMIN_NOM,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_PRENOM,
    DEFAULT_ADMIN_USERNAME,
)


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _ensure_default_admin() -> None:
    from core.security import hash_password
    from models.user import User, UserRole

    with SessionLocal() as session:
        existing_admin = session.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if existing_admin:
            return

        admin_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            nom=DEFAULT_ADMIN_NOM,
            prenom=DEFAULT_ADMIN_PRENOM,
            employee_code=DEFAULT_ADMIN_EMPLOYEE_CODE,
            telephone=None,
        )
        session.add(admin_user)
        session.commit()


def init_db() -> None:
    # Late import to ensure all models are registered on metadata.
    from models import (
        category,
        product,
        promotion,
        sale,
        sale_item,
        stock_movement,
        supplier,
        user,
    )

    _ = (category, product, promotion, sale, sale_item, stock_movement, supplier, user)
    Base.metadata.create_all(bind=engine)
    _ensure_default_admin()
